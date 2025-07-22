import { MapContainer, TileLayer, useMapEvents, Polyline } from 'react-leaflet';
import { useState } from 'react';
import axios from 'axios';

function RouteSelector({ onRoute }) {
  const [pts, setPts] = useState([]);
  useMapEvents({
    click(e) {
      const nextPts = [...pts, e.latlng];
      setPts(nextPts);
      console.log("クリック:", nextPts);

      if (nextPts.length === 2) {
        axios
          .get(`${process.env.REACT_APP_API_URL}/route`, {
            params: {
              start_lat: nextPts[0].lat,
              start_lng: nextPts[0].lng,
              end_lat: nextPts[1].lat,
              end_lng: nextPts[1].lng,
            },
          })
          .then(res => {
            const line = res.data.geometry.coordinates.map(([lng, lat]) => [lat, lng]);
            onRoute({ line, info: res.data });
            setPts([]); 
          })
          .catch(err => {
            console.error("経路取得エラー:", err);
            setPts([]); 
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
        <MapContainer center={[35.619264, 139.540682]} zoom={15} style={{ flex: 1 }}>
           <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
           <RouteSelector onRoute={setRouteData} />
           {routeData.line && <Polyline positions={routeData.line} />}
        </MapContainer>
        <div style={{ width: 300, padding: 16 }}>
          {routeData.info ? (
            <>
                <p><b>距離:</b> {(routeData.info.distance).toFixed(2)} km</p>
                <p><b>車:</b> {(routeData.info.car_time).toFixed(1)} 分 (40 km/h)</p>
                <p><b>自転車:</b> {(routeData.info.bike_time).toFixed(1)} 分 (15 km/h)</p>
                <p><b>徒歩:</b> {(routeData.info.walk_time).toFixed(1)} 分 (5 km/h)</p>
            </>
            
          ) : (
            <p>地図を2回クリックしてルートを取得</p>
          )}
        </div>
      </div>
    );
  }
