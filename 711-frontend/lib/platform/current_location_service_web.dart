// ignore_for_file: deprecated_member_use
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

import 'current_location_service_stub.dart';

Future<CurrentLocationResult> fetchCurrentLocation() async {
  final geolocation = html.window.navigator.geolocation;
  try {
    final position = await geolocation.getCurrentPosition(
      enableHighAccuracy: true,
      timeout: const Duration(seconds: 10),
      maximumAge: const Duration(seconds: 5),
    );
    final coords = position.coords;
    return CurrentLocationResult(
      lat: coords?.latitude?.toDouble(),
      lng: coords?.longitude?.toDouble(),
    );
  } catch (error) {
    final message = '$error';
    return CurrentLocationResult(
      error: message.contains('denied') || message.contains('PERMISSION_DENIED')
          ? '定位权限被拒绝，请在浏览器里允许定位。'
          : '定位失败，请刷新定位再试一次。',
      permissionDenied:
          message.contains('denied') || message.contains('PERMISSION_DENIED'),
    );
  }
}
