import asyncio
import httpx
from src.core.config.env import env

async def main():
    client = httpx.AsyncClient(base_url=env.SPTRANS_API_URL)
    auth = await client.post('/Login/Autenticar', params={'token': env.SPTRANS_API_TOKEN})
    print('Auth:', auth.json())
    res = await client.get('/Linha/Buscar', params={'termosBusca': '*'})
    data = res.json()
    print('Lines found:', len(data), 'Sample:', data[:1] if data else [])
    
    res_pos = await client.get('/Posicao')
    pos = res_pos.json()
    print('Global positions found:', type(pos), list(pos.keys())[:5] if isinstance(pos, dict) else [])
    if 'l' in pos:
        print('Number of lines active:', len(pos['l']))
        line = pos['l'][0]
        cl = line['cl']
        print(f"Fetching stops for line {cl}...")
        res_stops = await client.get('/Parada/BuscarParadasPorLinha', params={'codigoLinha': cl})
        if res_stops.status_code == 200:
            stops_line = res_stops.json()
            print('Stops for line:', len(stops_line), stops_line[:1])
        else:
            print('Error fetching stops by line:', res_stops.status_code, res_stops.text)

asyncio.run(main())
