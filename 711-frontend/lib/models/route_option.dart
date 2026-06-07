part of '../app_module.dart';

class _RouteOption {
  const _RouteOption({
    required this.id,
    required this.name,
    required this.label,
    required this.summary,
    required this.stops,
    required this.overloadLevel,
    required this.overloadHint,
  });

  final String id;
  final String name;
  final String label;
  final String summary;
  final List<_Stop> stops;
  final String overloadLevel;
  final String overloadHint;

  factory _RouteOption.fromAiRoute(
    Map<String, dynamic> json, {
    required String label,
    required String summary,
  }) {
    final stops = _stopsFromJson(json['stops'], aiFormat: true);
    return _RouteOption(
      id: '${json['route_id'] ?? label}',
      name: '${json['summary'] ?? label}',
      label: label,
      summary: summary,
      stops: stops,
      overloadLevel: _overloadLevel(stops),
      overloadHint: _overloadHint(_overloadLevel(stops)),
    );
  }

  String get metricLabel {
    final totalMinutes = stops.fold<int>(
      0,
      (sum, stop) =>
          sum +
          _minutesFromLabel(stop.duration) +
          _minutesFromLabel(stop.transit),
    );
    final totalDistanceKm =
        stops.length <= 1 ? 0.8 : 0.8 + (stops.length - 1) * 0.4;
    return '🚶 ${totalDistanceKm.toStringAsFixed(1)}km · ${(totalMinutes / 60).toStringAsFixed(1)}h';
  }

  static int _minutesFromLabel(String label) {
    final raw = RegExp(r'(\d+(?:\.\d+)?)').firstMatch(label)?.group(1);
    final value = double.tryParse(raw ?? '');
    if (value == null) return 0;
    return label.contains('h') || label.contains('小时')
        ? (value * 60).round()
        : value.round();
  }

  static String _overloadLevel(List<_Stop> stops) {
    final totalMinutes = stops.fold<int>(
      0,
      (sum, stop) =>
          sum +
          _minutesFromLabel(stop.duration) +
          _minutesFromLabel(stop.transit),
    );
    if (totalMinutes >= 300 || stops.length >= 5) return 'high';
    if (totalMinutes >= 240 || stops.length >= 4) return 'medium';
    return 'low';
  }

  static String _overloadHint(String level) {
    return switch (level) {
      'high' => '偏赶',
      'medium' => '稍满',
      _ => '轻松',
    };
  }

  static List<_Stop> _stopsFromJson(
    Object? value, {
    bool aiFormat = false,
  }) {
    if (value is! List) return const <_Stop>[];
    return [
      for (var i = 0; i < value.length; i++)
        if (value[i] is Map<String, dynamic>)
          _Stop.fromBackend(
            aiFormat
                ? _normalizeAiStop(value[i] as Map<String, dynamic>)
                : value[i] as Map<String, dynamic>,
            index: i,
          ),
    ];
  }

  static Map<String, dynamic> _normalizeAiStop(Map<String, dynamic> json) {
    final tags = json['tags'];
    return {
      'name': json['poi_name'],
      'category': json['category_sub'] ?? '地点',
      'time': json['arrival_time'],
      'dur': '约${json['stay_minutes'] ?? 60} 分',
      'meta': [
        if (json['rank_score'] != null) '评分 ${json['rank_score']}',
        if (tags is List) ...tags.map((item) => '$item'),
      ],
      'imgs': const ['📍'],
      'lat': json['lat'],
      'lng': json['lng'],
      'transitMode': json['transit_to_next_mode'],
      'transitMin': json['transit_to_next_minutes'],
    };
  }
}
