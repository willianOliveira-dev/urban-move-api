import asyncio
import logging
from datetime import datetime, timedelta, timezone

import uuid_utils as uuid
from sqlalchemy import delete, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.database import async_session_factory
from src.core.db.models.enums import TransportModal
from src.core.db.models.route import Route
from src.core.db.models.stop import Stop
from src.core.db.models.vehicle import Vehicle
from src.core.db.models.vehicle_position import VehiclePosition
from src.modules.mobility.sptrans.service import SPTransClient

logger = logging.getLogger("urbanmove.worker.sptrans")

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

BATCH_SIZE = 500


class SPTransWorker:
    """
    Worker responsável pela ingestão contínua de dados da SPTrans.

    Opera com dois loops independentes:
    - Posições (tempo real): atualiza rotas e veículos a cada 30 segundos via batch SQL.
    - Paradas (estático): sincroniza paradas de ônibus uma vez por dia.
    """

    def __init__(self) -> None:
        self._is_running = False
        self._processed_stops: set[str] = set()

    async def start(self, position_interval: int = 30, stops_interval_hours: int = 24) -> None:
        """Inicia ambos os loops de sincronização em paralelo."""
        self._is_running = True
        logger.info(
            "Worker SPTrans iniciado — posições a cada %ds, paradas a cada %dh.",
            position_interval,
            stops_interval_hours,
        )

        await asyncio.gather(
            self._position_loop(position_interval),
            self._stops_loop(stops_interval_hours),
        )

    def stop(self) -> None:
        self._is_running = False

    async def _position_loop(self, interval: int) -> None:
        """Loop rápido: sincroniza rotas, veículos e posições em tempo real."""
        while self._is_running:
            try:
                await self._sync_positions()
            except asyncio.CancelledError:
                self._is_running = False
                break
            except Exception as e:
                logger.error("Erro no loop de posições: %s", e)

            if self._is_running:
                await asyncio.sleep(interval)

    async def _stops_loop(self, interval_hours: int) -> None:
        """Loop lento: sincroniza paradas de ônibus periodicamente."""
        while self._is_running:
            try:
                await self._sync_all_stops()
            except asyncio.CancelledError:
                self._is_running = False
                break
            except Exception as e:
                logger.error("Erro no loop de paradas: %s", e)

            if self._is_running:
                await asyncio.sleep(interval_hours * 3600)

    async def _sync_positions(self) -> None:
        """Busca /Posicao e persiste rotas + veículos + posições via batch SQL."""
        client = SPTransClient()
        try:
            await client.authenticate()
            response = await client._client.get("/Posicao")
            response.raise_for_status()
            data = response.json()

            if "l" not in data:
                logger.warning("Payload de posições vazio.")
                return

            lines = data["l"]

            route_rows: list[dict[str, object]] = []
            vehicle_rows: list[dict[str, object]] = []
            position_rows: list[dict[str, object]] = []

            for line in lines:
                cl = str(line.get("cl"))
                c = str(line.get("c"))
                lt0 = str(line.get("lt0"))
                lt1 = str(line.get("lt1"))

                route_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"sptrans:route:{cl}"))

                route_rows.append({
                    "id": route_id,
                    "external_id": cl,
                    "short_name": c,
                    "long_name": f"{lt0} / {lt1}",
                    "terminal_primary": lt0,
                    "terminal_secondary": lt1,
                    "modal": TransportModal.BUS.value,
                    "color": "#0066CC",
                    "is_active": True,
                })

                vehicles_data = line.get("vs", [])
                for v in vehicles_data:
                    prefix = str(v.get("p"))
                    lat = v.get("py")
                    lng = v.get("px")
                    ta = v.get("ta")

                    try:
                        recorded_at = datetime.fromisoformat(ta.replace("Z", "+00:00"))
                    except (ValueError, TypeError, AttributeError):
                        recorded_at = datetime.now(timezone.utc)

                    vehicle_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"sptrans:vehicle:{prefix}"))
                    wkt = f"SRID=4326;POINT({lng} {lat})"

                    vehicle_rows.append({
                        "id": vehicle_id,
                        "external_id": prefix,
                        "prefix": prefix,
                        "route_id": route_id,
                        "modal": TransportModal.BUS.value,
                        "is_accessible": bool(v.get("a", False)),
                        "current_location_wkt": wkt,
                        "is_active": True,
                        "last_seen_at": recorded_at,
                    })

                    position_rows.append({
                        "vehicle_id": vehicle_id,
                        "location_wkt": wkt,
                        "recorded_at": recorded_at,
                    })

            async with async_session_factory() as session:
                await self._batch_upsert_routes(session, route_rows)
                await self._batch_upsert_vehicles(session, vehicle_rows)
                await self._batch_insert_positions(session, position_rows)
                await session.commit()
                await self._cleanup_old_data(session)

            logger.info("Posições sincronizadas — %d linhas, %d veículos.", len(route_rows), len(vehicle_rows))

        except Exception as e:
            logger.exception("Falha na sincronização de posições: %s", e)
        finally:
            await client.close()

    async def _batch_upsert_routes(self, session: AsyncSession, rows: list[dict[str, object]]) -> None:
        """Upsert de rotas em lotes usando raw SQL para máxima performance."""
        sql = text("""
            INSERT INTO routes (id, external_id, short_name, long_name, terminal_primary, terminal_secondary, modal, color, is_active, updated_at)
            VALUES (:id, :external_id, :short_name, :long_name, :terminal_primary, :terminal_secondary, :modal, :color, :is_active, now())
            ON CONFLICT (external_id) DO UPDATE SET
                is_active = EXCLUDED.is_active,
                updated_at = now()
        """)
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            await session.execute(sql, batch)

    async def _batch_upsert_vehicles(self, session: AsyncSession, rows: list[dict[str, object]]) -> None:
        """Upsert de veículos em lotes usando raw SQL para máxima performance."""
        sql = text("""
            INSERT INTO vehicles (id, external_id, prefix, route_id, modal, is_accessible, current_location, is_active, last_seen_at, updated_at)
            VALUES (:id, :external_id, :prefix, :route_id, :modal, :is_accessible, ST_GeogFromText(:current_location_wkt), :is_active, :last_seen_at, now())
            ON CONFLICT (external_id) DO UPDATE SET
                route_id = EXCLUDED.route_id,
                is_accessible = EXCLUDED.is_accessible,
                current_location = EXCLUDED.current_location,
                is_active = EXCLUDED.is_active,
                last_seen_at = EXCLUDED.last_seen_at,
                updated_at = now()
        """)
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            await session.execute(sql, batch)

    async def _batch_insert_positions(self, session: AsyncSession, rows: list[dict[str, object]]) -> None:
        """Insert de posições em lotes usando raw SQL para máxima performance."""
        sql = text("""
            INSERT INTO vehicle_positions (vehicle_id, location, recorded_at)
            VALUES (:vehicle_id, ST_GeogFromText(:location_wkt), :recorded_at)
        """)
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            await session.execute(sql, batch)

    async def _sync_all_stops(self) -> None:
        """Busca paradas de todas as linhas ativas e persiste no banco."""
        self._processed_stops.clear()
        logger.info("Iniciando sincronização completa de paradas...")

        client = SPTransClient()
        try:
            await client.authenticate()
            response = await client._client.get("/Posicao")
            response.raise_for_status()
            data = response.json()

            if "l" not in data:
                return

            lines = data["l"]
            stop_rows: list[dict[str, object]] = []

            for line in lines:
                line_code = str(line.get("cl"))
                new_rows = await self._fetch_stops_for_line(client, line_code)
                stop_rows.extend(new_rows)

            if stop_rows:
                async with async_session_factory() as session:
                    await self._batch_upsert_stops(session, stop_rows)
                    await session.commit()

            logger.info("Paradas sincronizadas — %d paradas únicas processadas.", len(stop_rows))

        except Exception as e:
            logger.exception("Falha na sincronização de paradas: %s", e)
        finally:
            await client.close()

    async def _fetch_stops_for_line(self, client: SPTransClient, line_code: str) -> list[dict[str, object]]:
        """Busca paradas de uma linha via HTTP e retorna dicts prontos para batch insert."""
        rows: list[dict[str, object]] = []
        try:
            res = await client._client.get(
                "/Parada/BuscarParadasPorLinha",
                params={"codigoLinha": line_code},
            )
            if res.status_code != 200:
                return rows

            for s in res.json():
                cp = str(s.get("cp"))
                if cp in self._processed_stops:
                    continue

                lat = s.get("py")
                lng = s.get("px")
                stop_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"sptrans:stop:{cp}"))

                rows.append({
                    "id": stop_id,
                    "external_id": cp,
                    "name": str(s.get("np")) or "Parada",
                    "modal": TransportModal.BUS.value,
                    "location_wkt": f"SRID=4326;POINT({lng} {lat})",
                    "is_accessible": False,
                })
                self._processed_stops.add(cp)

        except Exception as e:
            logger.debug("Erro ao buscar paradas da linha %s: %s", line_code, e)

        return rows

    async def _batch_upsert_stops(self, session: AsyncSession, rows: list[dict[str, object]]) -> None:
        """Upsert de paradas em lotes usando raw SQL para máxima performance."""
        sql = text("""
            INSERT INTO stops (id, external_id, name, modal, location, is_accessible)
            VALUES (:id, :external_id, :name, :modal, ST_GeogFromText(:location_wkt), :is_accessible)
            ON CONFLICT (external_id) DO UPDATE SET
                location = EXCLUDED.location
        """)
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            await session.execute(sql, batch)

    async def _cleanup_old_data(self, session: AsyncSession) -> None:
        """
        Política de retenção para o plano gratuito do Supabase (500MB).
        Posições: retenção de 2 horas.
        Entidades inativas: desativadas após 24 horas.
        """
        now_utc = datetime.now(timezone.utc)
        cutoff_positions = now_utc - timedelta(hours=2)
        cutoff_entities = now_utc - timedelta(hours=24)

        stmt_del = delete(VehiclePosition).where(VehiclePosition.recorded_at < cutoff_positions)
        res_del = await session.execute(stmt_del)

        stmt_routes = update(Route).where(Route.updated_at < cutoff_entities).values(is_active=False)
        res_routes = await session.execute(stmt_routes)

        stmt_vehicles = update(Vehicle).where(Vehicle.updated_at < cutoff_entities).values(is_active=False)
        res_vehicles = await session.execute(stmt_vehicles)

        await session.commit()

        if res_del.rowcount or res_routes.rowcount or res_vehicles.rowcount:
            logger.info(
                "Limpeza: %d posições deletadas, %d rotas e %d veículos desativados.",
                res_del.rowcount,
                res_routes.rowcount,
                res_vehicles.rowcount,
            )
