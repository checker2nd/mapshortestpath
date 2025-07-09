import { MapContainer, TileLayer, useMapEvents, Polyline } from 'react-leaflet';
import { useState } from 'react';
import axios from 'axios';

function RouteSelector({ onRoute }) {
  const [pts, setPts] = useState([]);
  useMapEvents({
    click(e) {
      const next = [...pts, e.latlng];
      setPts(next);
      if (next.length === 2) {
        axios
          .get(`${process.env.REACT_APP_API_URL}/route`, {
            params: {
              start_lat: next[0].lat,
              start_lng: next[0].lng,
              end_lat: next[1].lat,
              end_lng: next[1].lng,
            },
          })
          .then(res => {
            const line = res.data.geometry.coordinates.map(([lng, lat]) => [lat, lng]);
            onRoute({ line, info: res.data });
          });
      }
    },
  });
  return null;
}

export default function App() {
  const [routeData, setRouteData] = useState({ line: null, info: null });

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <MapContainer center={[35.68, 139.76]} zoom={13} style={{ flex: 1 }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <RouteSelector onRoute={setRouteData} />
        {routeData.line && <Polyline positions={routeData.line} />}
      </MapContainer>
      <div style={{ width: 300, padding: 16 }}>
        {routeData.info ? (
          <>
            <p>距離: {(routeData.info.distance / 1000).toFixed(2)} km</p>
            <p>所要時間: {(routeData.info.duration / 60).toFixed(1)} 分</p>
          </>
        ) : (
          <p>地図を2回クリックしてルートを取得</p>
        )}
      </div>
    </div>
  );
}
