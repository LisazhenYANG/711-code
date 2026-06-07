part of '../../app_module.dart';

class _RouteMap extends StatelessWidget {
  const _RouteMap({
    required this.stops,
    this.currentLat,
    this.currentLng,
  });

  final List<_Stop> stops;
  final double? currentLat;
  final double? currentLng;

  @override
  Widget build(BuildContext context) {
    final mappedStops = [
      for (final stop in stops)
        if (stop.lat != null && stop.lng != null)
          {
            'name': stop.name,
            'category': stop.category,
            'lat': stop.lat,
            'lng': stop.lng,
          },
    ];
    if (mappedStops.isEmpty) {
      return CustomPaint(painter: _MapPainter(), child: const _MapNodes());
    }
    final currentLocation = currentLat != null && currentLng != null
        ? {
            'lat': currentLat,
            'lng': currentLng,
          }
        : null;
    return ClipRRect(
      borderRadius: BorderRadius.circular(24),
      child: buildAmapRouteView(mappedStops, currentLocation: currentLocation),
    );
  }
}

class _MapPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final bgPaint = Paint()..color = const Color(0xFFF0E8DC);
    canvas.drawRRect(
      RRect.fromRectAndRadius(Offset.zero & size, const Radius.circular(24)),
      bgPaint,
    );

    final roadPaint = Paint()
      ..color = Colors.white.withValues(alpha: .55)
      ..strokeWidth = 18
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    for (final y in [44.0, 112.0, 188.0]) {
      canvas.drawLine(
          Offset(-20, y), Offset(size.width + 20, y + 38), roadPaint);
    }

    final routePaint = Paint()
      ..color = _brown.withValues(alpha: .55)
      ..strokeWidth = 7
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    final path = Path()
      ..moveTo(size.width * .24, size.height * .28)
      ..cubicTo(size.width * .42, size.height * .16, size.width * .62,
          size.height * .43, size.width * .78, size.height * .38)
      ..cubicTo(size.width * .64, size.height * .56, size.width * .48,
          size.height * .70, size.width * .34, size.height * .78);
    canvas.drawPath(path, routePaint);

    final metroPaint = Paint()
      ..color = _metro.withValues(alpha: .38)
      ..strokeWidth = 5
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    canvas.drawLine(Offset(size.width * .77, size.height * .40),
        Offset(size.width * .36, size.height * .77), metroPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _MapNodes extends StatelessWidget {
  const _MapNodes();

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: const [
        Positioned(
            left: 72,
            top: 52,
            child: _MapNode(num: '1', icon: '✂️', color: _brown)),
        Positioned(
            right: 54,
            top: 88,
            child: _MapNode(num: '2', icon: '🎨', color: _metro)),
        Positioned(
            left: 112,
            bottom: 34,
            child: _MapNode(num: '3', icon: '📚', color: _green)),
        Positioned(
            left: 18, bottom: 18, child: _SoftPill(label: '静安寺 · 南京西路 · 苏河湾')),
      ],
    );
  }
}
