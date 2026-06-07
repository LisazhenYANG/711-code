// ignore_for_file: deprecated_member_use

// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'dart:convert';
import 'dart:ui_web' as ui_web;

import 'package:flutter/widgets.dart';

const String _amapWebKey = String.fromEnvironment(
  'AMAP_WEB_KEY',
  defaultValue: 'ad60231527de01346ff42986cf9db6bc',
);
const String _amapSecurityCode = String.fromEnvironment(
  'AMAP_SECURITY_CODE',
  defaultValue: '160ec6f3657d17ee36c316ce6baff3f7',
);

int _viewSeq = 0;

Widget buildAmapRouteView(
  List<Map<String, Object?>> stops, {
  Map<String, Object?>? currentLocation,
}) {
  final viewType = 'manyou-amap-route-${_viewSeq++}';
  final htmlStops = jsonEncode(stops).replaceAll('</', '<\\/');
  final htmlCurrent =
      jsonEncode(currentLocation).replaceAll('</', '<\\/');
  ui_web.platformViewRegistry.registerViewFactory(viewType, (int viewId) {
    final iframe = html.IFrameElement()
      ..style.border = '0'
      ..style.width = '100%'
      ..style.height = '100%'
      ..style.display = 'block'
      ..allow = 'geolocation'
      ..srcdoc = _mapDocument(htmlStops, htmlCurrent);
    return iframe;
  });
  return HtmlElementView(viewType: viewType);
}

String _mapDocument(String stopsJson, String currentJson) {
  return '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    html, body, #map { width: 100%; height: 100%; margin: 0; overflow: hidden; }
    body { background: #f0e8dc; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; }
    .marker-wrap {
      position: relative;
      display: inline-flex;
      flex-direction: column;
      align-items: center;
    }
    .marker {
      min-width: 28px;
      height: 28px;
      border-radius: 999px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-weight: 800;
      font-size: 13px;
      background: #8b5e3c;
      border: 2px solid rgba(255,255,255,.95);
      box-shadow: 0 6px 16px rgba(80,52,25,.25);
    }
    .label {
      position: absolute;
      left: 50%;
      top: 34px;
      transform: translateX(-50%);
      padding: 3px 7px;
      max-width: 132px;
      border-radius: 999px;
      background: rgba(255,250,243,.94);
      color: #3d3329;
      border: 1px solid rgba(139,94,60,.22);
      box-shadow: 0 4px 12px rgba(70,45,18,.14);
      font-size: 11px;
      line-height: 1.2;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      pointer-events: none;
    }
    .marker-wrap.label-top .label {
      top: auto;
      bottom: 34px;
    }
    .marker-wrap.label-left .label {
      left: auto;
      right: 20px;
      top: 50%;
      bottom: auto;
      transform: translateY(-50%);
    }
    .marker-wrap.label-right .label {
      left: 20px;
      top: 50%;
      bottom: auto;
      transform: translateY(-50%);
    }
    .marker-wrap.label-hidden .label {
      display: none;
    }
    .fallback {
      height: 100%;
      display: grid;
      place-items: center;
      color: #7a6a58;
      font-size: 13px;
    }
    .you-dot {
      width: 18px;
      height: 18px;
      border-radius: 999px;
      background: #3a7afe;
      border: 3px solid rgba(255,255,255,.95);
      box-shadow: 0 0 0 8px rgba(58,122,254,.16);
    }
  </style>
  <script>
    window._AMapSecurityConfig = { securityJsCode: '$_amapSecurityCode' };
  </script>
  <script src="https://webapi.amap.com/maps?v=2.0&key=$_amapWebKey&plugin=AMap.Scale,AMap.ToolBar"></script>
</head>
<body>
  <div id="map"><div class="fallback">地图加载中...</div></div>
  <script>
    const stops = $stopsJson;
    const currentLocation = $currentJson;
    function validStop(stop) {
      return Number.isFinite(Number(stop.lat)) && Number.isFinite(Number(stop.lng));
    }
    function init() {
      if (!window.AMap) {
        document.getElementById('map').innerHTML = '<div class="fallback">高德地图加载失败，请检查 Web Key 和网络</div>';
        return;
      }
      const points = stops.filter(validStop).map((stop, index) => ({
        ...stop,
        index,
        lnglat: [Number(stop.lng), Number(stop.lat)]
      }));
      if (!points.length) {
        document.getElementById('map').innerHTML = '<div class="fallback">当前路线没有坐标</div>';
        return;
      }
      const map = new AMap.Map('map', {
        zoom: 14,
        center: currentLocation && validStop(currentLocation)
          ? [Number(currentLocation.lng), Number(currentLocation.lat)]
          : points[0].lnglat,
        viewMode: '2D',
        mapStyle: 'amap://styles/normal'
      });
      map.addControl(new AMap.Scale());
      map.addControl(new AMap.ToolBar({ position: 'RB' }));
      const path = points.map((point) => point.lnglat);
      if (path.length > 1) {
        new AMap.Polyline({
          map,
          path,
          strokeColor: '#8b5e3c',
          strokeWeight: 6,
          strokeOpacity: 0.82,
          lineJoin: 'round',
          lineCap: 'round'
        });
      }
      const overlays = [];
      if (currentLocation && validStop(currentLocation)) {
        const currentLngLat = [Number(currentLocation.lng), Number(currentLocation.lat)];
        const currentMarker = new AMap.Marker({
          map,
          position: currentLngLat,
          content: '<div class="you-dot"></div>',
          anchor: 'center',
          title: '你的位置'
        });
        overlays.push(currentMarker);
        if (path.length) {
          const approachLine = new AMap.Polyline({
            map,
            path: [currentLngLat, path[0]],
            strokeColor: '#3a7afe',
            strokeWeight: 5,
            strokeOpacity: 0.72,
            strokeStyle: 'dashed',
            lineJoin: 'round',
            lineCap: 'round'
          });
          overlays.push(approachLine);
        }
      }
      const placements = ['label-bottom', 'label-top', 'label-right', 'label-left'];
      const placed = [];
      function distance(a, b) {
        return Math.hypot(a.x - b.x, a.y - b.y);
      }
      function pickPlacement(pixel) {
        const nearby = placed.filter((item) => distance(item.pixel, pixel) < 72);
        if (nearby.length >= 3) return 'label-hidden';
        const used = new Set(nearby.map((item) => item.placement));
        for (const placement of placements) {
          if (!used.has(placement)) return placement;
        }
        return placements[nearby.length % placements.length];
      }
      points.forEach((point, index) => {
        const markerContent = document.createElement('div');
        const pixel = map.lngLatToContainer(point.lnglat);
        const placement = pickPlacement(pixel);
        markerContent.className = 'marker-wrap ' + placement;
        markerContent.innerHTML = '<div class="marker">' + (index + 1) + '</div><div class="label">' + point.name + '</div>';
        new AMap.Marker({
          map,
          position: point.lnglat,
          content: markerContent,
          anchor: 'bottom-center',
          title: point.name
        });
        placed.push({ pixel, placement });
      });
      map.setFitView();
    }
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  </script>
</body>
</html>
''';
}
