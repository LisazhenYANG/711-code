part of '../app_module.dart';

class _ManyouApi {
  const _ManyouApi();

  static const String _baseUrl = String.fromEnvironment(
    'MANYOU_API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );
  static const String _aiBaseUrl = String.fromEnvironment(
    'MANYOU_AI_BASE_URL',
    defaultValue: 'http://127.0.0.1:8001',
  );

  Future<List<_Stop>> generateRoute({
    required List<String> moods,
    required List<String> discoverItems,
    String freeText = '',
  }) async {
    final uri = Uri.parse('$_baseUrl/api/routes/generate');
    final response = await http.post(
      uri,
      headers: const {'Content-Type': 'application/json'},
      body: jsonEncode({
        'location': const {'city': '上海', 'area': '静安区'},
        'time_slot': _guessTimeSlot(freeText),
        'people': _guessPeople(freeText),
        'moods': moods.isEmpty ? const ['静下来'] : moods,
        'discover_items': discoverItems,
        'user_profile': {'free_text': freeText},
      }),
    );

    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('Route API ${response.statusCode}: ${response.body}');
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final routes = data['routes'];
    if (routes is! List || routes.isEmpty) {
      throw Exception('Route API returned no routes');
    }

    final route = routes.first as Map<String, dynamic>;
    final stops = route['stops'];
    if (stops is! List || stops.isEmpty) {
      throw Exception('Route API returned no stops');
    }

    return [
      for (var i = 0; i < stops.length; i++)
        _Stop.fromBackend(stops[i] as Map<String, dynamic>, index: i),
    ];
  }

  Stream<_RoutePlanStreamEvent> streamGenerateRoute({
    required List<String> moods,
    required List<String> discoverItems,
    String freeText = '',
  }) async* {
    final client = http.Client();
    try {
      final request = http.Request(
        'POST',
        Uri.parse('$_aiBaseUrl/plan/stream'),
      );
      request.headers['Content-Type'] = 'application/json';
      request.body = jsonEncode({
        'user_id': 'demo-user',
        'intent': {
          'origin_lat': 31.2304,
          'origin_lng': 121.4737,
          'origin_name': '上海',
          'time_slot': _guessTimeSlot(freeText),
          'people_count': _guessPeopleCount(freeText),
          'transport_mode': 'transit',
          'moods': moods.isEmpty ? const ['静下来'] : moods,
          'sub_categories': discoverItems,
          'free_text': freeText,
          'city_code': '021',
        },
        'weather': const {'condition': '晴'},
      });
      final response = await client.send(request);
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw Exception('Plan stream ${response.statusCode}');
      }
      final lines = response.stream
          .transform(utf8.decoder)
          .transform(const LineSplitter());
      await for (final line in lines) {
        if (line.trim().isEmpty) continue;
        final data = jsonDecode(line) as Map<String, dynamic>;
        final type = '${data['type'] ?? 'status'}';
        if (type == 'final') {
          final payload = data['payload'];
          final payloadMap =
              payload is Map<String, dynamic> ? payload : const <String, dynamic>{};
          final stops = payloadMap['stops'];
          yield _RoutePlanStreamEvent(
            message: '${data['message'] ?? '我已经整理好一版今日路线。'}',
            done: true,
            stops: stops is List
                ? [
                    for (var i = 0; i < stops.length; i++)
                      if (stops[i] is Map<String, dynamic>)
                        _Stop.fromBackend(stops[i] as Map<String, dynamic>, index: i),
                  ]
                : const [],
          );
        } else if (type == 'error') {
          throw Exception('${data['message'] ?? 'stream failed'}');
        } else {
          yield _RoutePlanStreamEvent(
            message: '${data['message'] ?? '正在生成路线...'}',
          );
        }
      }
    } finally {
      client.close();
    }
  }

  Future<Map<String, dynamic>> dashboard() async {
    return _getMap('/api/dashboard');
  }

  Future<List<_RecommendationItem>> recommendations() async {
    final data = await _getMap('/api/recommendations');
    final items = data['recommendations'];
    if (items is! List) return const [];
    return [
      for (final item in items)
        if (item is Map<String, dynamic>) _RecommendationItem.fromJson(item),
    ];
  }

  Future<List<_RecommendationItem>> nearbyPlaceRecommendations(
    List<_Stop> route,
  ) async {
    final response = await http.get(Uri.parse('$_aiBaseUrl/pois'));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('POIs ${response.statusCode}');
    }
    final data = jsonDecode(response.body);
    if (data is! List) return const [];
    final routeWithCoords = [
      for (final stop in route)
        if (stop.lat != null && stop.lng != null) stop,
    ];
    final existingNames = {for (final stop in route) stop.name};
    final scored = <({double distanceKm, Map<String, dynamic> poi})>[];
    for (final item in data) {
      if (item is! Map<String, dynamic>) continue;
      final name = '${item['name'] ?? ''}';
      if (name.isEmpty || existingNames.contains(name)) continue;
      final lat = _number(item['lat']);
      final lng = _number(item['lng']);
      if (lat == null || lng == null) continue;
      final distanceKm = routeWithCoords.isEmpty
          ? 0
          : routeWithCoords
              .map((stop) => _haversineKm(stop.lat!, stop.lng!, lat, lng))
              .reduce(math.min);
      if (routeWithCoords.isNotEmpty && distanceKm > 3.0) continue;
      scored.add((distanceKm: distanceKm.toDouble(), poi: item));
    }
    scored.sort((a, b) => a.distanceKm.compareTo(b.distanceKm));
    return [
      for (final entry in scored.take(6))
        _RecommendationItem(
          icon: _Stop._categoryIcon('${entry.poi['category_sub'] ?? ''}'),
          title: '${entry.poi['name'] ?? ''}',
          subtitle:
              '${entry.poi['category_sub'] ?? entry.poi['category_main'] ?? '地点'} · ${entry.distanceKm.toStringAsFixed(1)}km',
          rating: '★ ${_number(entry.poi['rank_score'])?.toStringAsFixed(1) ?? '4.6'}',
          price: '',
          duration: '约 ${entry.poi['stay_minutes'] ?? 60} 分',
          gallery: [_Stop._categoryIcon('${entry.poi['category_sub'] ?? ''}')],
          reason: '离当前路线较近，顺路加入不会绕太远。',
        ),
    ];
  }

  Future<_UserProfileData> profile(String userId) async {
    final data = await _getMap('/api/preferences/$userId');
    return _UserProfileData.fromJson(data);
  }

  Future<List<_MealRestaurant>> mealRestaurants({
    required double lat,
    required double lng,
    required String slot,
  }) async {
    final uri = Uri.parse(
      '$_aiBaseUrl/restaurants?lat=$lat&lng=$lng&slot=$slot&radius_m=5000&limit=8',
    );
    final response = await http.get(uri);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('Restaurants ${response.statusCode}');
    }
    final data = jsonDecode(response.body);
    if (data is! List) return const [];
    return [
      for (final item in data)
        if (item is Map<String, dynamic>) _MealRestaurant.fromJson(item),
    ];
  }

  Future<List<_BookingItem>> checkoutBookings(List<_BookingItem> items) async {
    final data = await _postMap('/api/bookings/checkout', {
      'items': [for (final item in items) item.toCheckoutJson()],
    });
    final results = data['results'];
    if (results is! List) return items;
    return [
      for (var i = 0; i < results.length; i++)
        if (results[i] is Map<String, dynamic>)
          _BookingItem.fromJson({
            'icon': i < items.length ? items[i].icon : null,
            ...results[i] as Map<String, dynamic>,
          }),
    ];
  }

  Future<Map<String, dynamic>> routeAction({
    required String action,
    required List<_Stop> route,
    required Set<int> lockedIndexes,
    required Set<int> hiddenIndexes,
    int? index,
    String value = '',
    int? recommendationIndex,
    List<String> priorities = const [],
  }) async {
    return _postMap('/api/route/action', {
      'action': action,
      'route': [for (final stop in route) stop.toBackendJson()],
      'lockedIndexes': lockedIndexes.toList(),
      'hiddenIndexes': hiddenIndexes.toList(),
      if (index != null) 'index': index,
      if (value.isNotEmpty) 'value': value,
      if (recommendationIndex != null)
        'recommendationIndex': recommendationIndex,
      'priorities': priorities,
    });
  }

  Stream<_ChatStreamEvent> streamAiChat({
    required String message,
    required List<_Stop> route,
  }) async* {
    final client = http.Client();
    try {
      final request = http.Request(
        'POST',
        Uri.parse('$_aiBaseUrl/chat/stream'),
      );
      request.headers['Content-Type'] = 'application/json';
      request.body = jsonEncode({
        'user_id': 'demo-user',
        'message': message,
        'current_route': [for (final stop in route) _stopToAiJson(stop)],
        'weather': const {'condition': '晴'},
        'intent_context': {
          'origin_lat': 31.2304,
          'origin_lng': 121.4737,
          'origin_name': '上海',
          'time_slot': '下午',
          'people_count': 2,
          'transport_mode': 'transit',
        },
      });
      final response = await client.send(request);
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw Exception('AI stream ${response.statusCode}');
      }

      final lines = response.stream
          .transform(utf8.decoder)
          .transform(const LineSplitter());
      await for (final line in lines) {
        if (line.trim().isEmpty) continue;
        final data = jsonDecode(line) as Map<String, dynamic>;
        final type = '${data['type'] ?? 'status'}';
        if (type == 'final') {
          final payload = data['payload'];
          final payloadMap =
              payload is Map<String, dynamic> ? payload : const <String, dynamic>{};
          final recommendations = payloadMap['recommendations'];
          yield _ChatStreamEvent(
            message: '${data['message'] ?? '我已经处理好了。'}',
            done: true,
            intent: '${payloadMap['intent'] ?? ''}',
            updatedStops: _updatedStopsFromAiPayload(payloadMap),
            recommendations: recommendations is List
                ? [
                    for (final item in recommendations)
                      if (item is Map<String, dynamic>)
                        _RecommendationItem(
                          icon: _Stop._categoryIcon(
                              '${item['category_sub'] ?? item['category'] ?? ''}'),
                          title:
                              '${item['name'] ?? item['poi_name'] ?? '推荐地点'}',
                          subtitle:
                              '${item['category_sub'] ?? item['category_main'] ?? '地点'}',
                          rating: '★ ${_number(item['rank_score'])?.toStringAsFixed(1) ?? '4.6'}',
                          price: '',
                          duration:
                              '约 ${((item['stay_minutes'] is num) ? item['stay_minutes'] : 60)} 分',
                          gallery: [
                            _Stop._categoryIcon(
                                '${item['category_sub'] ?? item['category'] ?? ''}')
                          ],
                          reason: '${item['reason'] ?? '可以加入当前路线。'}',
                        ),
                  ]
                : const [],
          );
        } else if (type == 'error') {
          throw Exception('${data['message'] ?? 'stream failed'}');
        } else {
          yield _ChatStreamEvent(
            message: '${data['message'] ?? '正在处理...'}',
          );
        }
      }
    } finally {
      client.close();
    }
  }

  Future<Map<String, dynamic>> _getMap(String path) async {
    final response = await http.get(Uri.parse('$_baseUrl$path'));
    return _decodeMap(response);
  }

  Future<Map<String, dynamic>> _postMap(
      String path, Map<String, dynamic> body) async {
    final response = await http.post(
      Uri.parse('$_baseUrl$path'),
      headers: const {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    return _decodeMap(response);
  }

  Map<String, dynamic> _decodeMap(http.Response response) {
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('API ${response.statusCode}: ${response.body}');
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  String _guessTimeSlot(String text) {
    if (text.contains('上午') || text.contains('早上')) return '上午';
    if (text.contains('全天') || text.contains('一天')) return '全天';
    if (text.contains('晚上') || text.contains('晚餐')) return '随时';
    return '下午';
  }

  String _guessPeople(String text) {
    if (text.contains('一个人') || text.contains('自己')) return '1人';
    if (text.contains('三个人') || text.contains('3人')) return '3人';
    if (text.contains('四个人') || text.contains('4人')) return '4人';
    return '2人';
  }

  int _guessPeopleCount(String text) {
    if (text.contains('一个人') || text.contains('自己')) return 1;
    if (text.contains('三个人') || text.contains('3人')) return 3;
    if (text.contains('四个人') || text.contains('4人')) return 4;
    return 2;
  }

  Map<String, dynamic> _stopToAiJson(_Stop stop) {
    return {
      'poi_id': stop.name,
      'poi_name': stop.name,
      'category_sub': stop.category,
      'lat': stop.lat ?? 31.2304,
      'lng': stop.lng ?? 121.4737,
      'stay_minutes': _durationMinutes(stop.duration),
      'transit_to_next_minutes': _transitMinutes(stop.transit),
      'transit_to_next_mode': _transitMode(stop.transit),
      'locked': false,
      'indoor': !stop.category.contains('草坪'),
      'note': stop.note,
    };
  }

  int _durationMinutes(String label) {
    final value = RegExp(r'(\d+(?:\.\d+)?)').firstMatch(label)?.group(1);
    if (value == null) return 60;
    final number = double.tryParse(value) ?? 1;
    return label.contains('h') || label.contains('小时')
        ? (number * 60).round()
        : number.round();
  }

  int _transitMinutes(String label) {
    return int.tryParse(RegExp(r'(\d+)').firstMatch(label)?.group(1) ?? '') ?? 0;
  }

  String _transitMode(String label) {
    if (label.contains('地铁')) return 'transit';
    if (label.contains('打车')) return 'drive';
    return 'walk';
  }

  List<_Stop> _updatedStopsFromAiPayload(Map<String, dynamic> payload) {
    final updatedRoute = payload['updated_route'];
    if (updatedRoute is! List) return const [];
    return [
      for (var i = 0; i < updatedRoute.length; i++)
        if (updatedRoute[i] is Map<String, dynamic>)
          _Stop.fromBackend(
            _aiStopToFrontendJson(updatedRoute[i] as Map<String, dynamic>),
            index: i,
          ),
    ];
  }

  Map<String, dynamic> _aiStopToFrontendJson(Map<String, dynamic> stop) {
    return {
      'name': stop['poi_name'] ?? stop['name'] ?? '未命名地点',
      'category': stop['category_sub'] ?? '地点',
      'time': stop['arrival_time'] ?? '待定',
      'dur': _minutesToDuration(stop['stay_minutes']),
      'meta': [
        if (stop['note'] != null) '${stop['note']}',
        if (stop['locked'] == true) '已锁定',
      ],
      'imgs': [_Stop._categoryIcon('${stop['category_sub'] ?? ''}')],
      'transitMode': stop['transit_to_next_mode'],
      'transitMin': stop['transit_to_next_minutes'],
      'lat': stop['lat'],
      'lng': stop['lng'],
    };
  }

  String _minutesToDuration(Object? minutes) {
    final value = minutes is num ? minutes.toInt() : 60;
    if (value >= 60) {
      final hours = value / 60;
      return hours == hours.roundToDouble()
          ? '约 ${hours.toStringAsFixed(0)}h'
          : '约 ${hours.toStringAsFixed(1)}h';
    }
    return '约 $value 分';
  }

  double? _number(Object? value) {
    if (value is num) return value.toDouble();
    return double.tryParse('$value');
  }

  double _haversineKm(double lat1, double lng1, double lat2, double lng2) {
    const earthRadiusKm = 6371.0;
    final dLat = _degToRad(lat2 - lat1);
    final dLng = _degToRad(lng2 - lng1);
    final a =
        math.sin(dLat / 2) * math.sin(dLat / 2) +
            math.cos(_degToRad(lat1)) *
                math.cos(_degToRad(lat2)) *
                math.sin(dLng / 2) *
                math.sin(dLng / 2);
    final c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
    return earthRadiusKm * c;
  }

  double _degToRad(double degrees) => degrees * (math.pi / 180);
}

class _ChatStreamEvent {
  const _ChatStreamEvent({
    required this.message,
    this.done = false,
    this.updatedStops = const [],
    this.recommendations = const [],
    this.intent = '',
  });

  final String message;
  final bool done;
  final List<_Stop> updatedStops;
  final List<_RecommendationItem> recommendations;
  final String intent;
}

class _RoutePlanStreamEvent {
  const _RoutePlanStreamEvent({
    required this.message,
    this.done = false,
    this.stops = const [],
  });

  final String message;
  final bool done;
  final List<_Stop> stops;
}
