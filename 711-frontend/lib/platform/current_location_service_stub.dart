class CurrentLocationResult {
  const CurrentLocationResult({
    this.lat,
    this.lng,
    this.error,
    this.permissionDenied = false,
  });

  final double? lat;
  final double? lng;
  final String? error;
  final bool permissionDenied;

  bool get hasLocation => lat != null && lng != null;
}

Future<CurrentLocationResult> fetchCurrentLocation() async {
  return const CurrentLocationResult(
    error: '当前平台暂不支持实时定位。',
  );
}
