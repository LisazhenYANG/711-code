part of '../app_module.dart';

class _BookingItem {
  const _BookingItem({
    required this.icon,
    required this.name,
    required this.category,
    required this.bookingType,
    required this.time,
    required this.statusText,
    this.productName = '',
    this.price = '',
    this.code = '',
    this.done = false,
  });

  final String icon;
  final String name;
  final String category;
  final String bookingType;
  final String time;
  final String statusText;
  final String productName;
  final String price;
  final String code;
  final bool done;

  String get subtitle {
    final parts = [
      if (productName.isNotEmpty) productName,
      if (price.isNotEmpty) price,
      if (time.isNotEmpty) time,
      if (code.isNotEmpty) code,
    ];
    return parts.join(' · ');
  }

  Map<String, dynamic> toCheckoutJson() {
    return {
      'name': name,
      'category': category,
      'bookingType': bookingType,
      'time': time,
      'paid': done,
      'selectedProduct': {
        'name': productName.isEmpty ? bookingType : productName,
        'price': price,
      },
    };
  }

  factory _BookingItem.fromJson(Map<String, dynamic> json) {
    final product = json['selectedProduct'];
    final productMap = product is Map<String, dynamic> ? product : const {};
    final status = '${json['status'] ?? ''}';
    return _BookingItem(
      icon:
          '${json['icon'] ?? _Stop._categoryIcon('${json['category'] ?? ''}')}',
      name: '${json['name'] ?? ''}',
      category: '${json['category'] ?? ''}',
      bookingType: '${json['bookingType'] ?? '预约'}',
      time: '${json['ticketTime'] ?? json['time'] ?? ''}',
      statusText: '${json['statusText'] ?? _statusText(status)}',
      productName: '${productMap['name'] ?? ''}',
      price: '${json['ticketPrice'] ?? productMap['price'] ?? ''}',
      code: '${json['code'] ?? ''}',
      done:
          status == 'purchased' || status == 'confirmed' || json['qr'] == true,
    );
  }

  static String _statusText(String status) {
    return switch (status) {
      'purchased' => '已购票',
      'confirmed' => '已预约',
      'pending' => '待处理',
      _ => '待处理',
    };
  }
}

class _MealRestaurant {
  const _MealRestaurant({
    required this.id,
    required this.name,
    required this.icon,
    required this.subtitle,
  });

  final String id;
  final String name;
  final String icon;
  final String subtitle;

  factory _MealRestaurant.fromJson(Map<String, dynamic> json) {
    final cuisine = '${json['cuisine'] ?? json['sub_category'] ?? '餐厅'}';
    final rating = _number(json['rating']);
    final avgPrice = _number(json['avg_price']);
    final distance = _number(json['distance_m']);
    final parts = <String>[
      cuisine,
      if (rating != null && rating > 0) '★ ${rating.toStringAsFixed(1)}',
      if (avgPrice != null && avgPrice > 0) '人均 ¥${avgPrice.round()}',
      if (distance != null && distance > 0)
        distance >= 1000
            ? '${(distance / 1000).toStringAsFixed(1)}km'
            : '${distance.round()}m',
    ];
    return _MealRestaurant(
      id: '${json['id'] ?? ''}',
      name: '${json['name'] ?? ''}',
      icon: _iconForCuisine(cuisine),
      subtitle: parts.join(' · '),
    );
  }

  static double? _number(Object? value) {
    if (value is num) return value.toDouble();
    return double.tryParse('$value');
  }

  static String _iconForCuisine(String cuisine) {
    if (cuisine.contains('日')) return '🍣';
    if (cuisine.contains('西')) return '🍽️';
    if (cuisine.contains('粤')) return '🥢';
    if (cuisine.contains('火锅')) return '🍲';
    if (cuisine.contains('烧烤') || cuisine.contains('烧鸟')) return '🍢';
    if (cuisine.contains('咖啡')) return '☕';
    return '🍜';
  }
}

class _PlanSummary {
  const _PlanSummary({
    required this.title,
    required this.status,
    required this.duration,
    required this.todos,
  });

  final String title;
  final String status;
  final String duration;
  final List<Map<String, dynamic>> todos;

  factory _PlanSummary.fromJson(Map<String, dynamic> json) {
    return _PlanSummary(
      title: '${json['title'] ?? '今日路线'}',
      status: '${json['status'] ?? '进行中'}',
      duration: '${json['duration'] ?? '半天'}',
      todos: _maps(json['todos']),
    );
  }

  static List<Map<String, dynamic>> _maps(Object? value) {
    if (value is! List) return const [];
    return [
      for (final item in value)
        if (item is Map<String, dynamic>) item,
    ];
  }
}

class _WeatherSummary {
  const _WeatherSummary({
    required this.dateLabel,
    required this.locationLabel,
    required this.temperatureLabel,
    required this.conditionLabel,
    required this.rainLabel,
  });

  final String dateLabel;
  final String locationLabel;
  final String temperatureLabel;
  final String conditionLabel;
  final String rainLabel;

  factory _WeatherSummary.fromDashboard(Map<String, dynamic> json) {
    final weather = json['weather'];
    final weatherMap = weather is Map<String, dynamic> ? weather : const {};
    return _WeatherSummary(
      dateLabel: '${json['date'] ?? '今天'}',
      locationLabel: '${json['location'] ?? '上海·静安区'}',
      temperatureLabel: '${weatherMap['temp'] ?? '--'}',
      conditionLabel: '${weatherMap['condition'] ?? '天气良好'}',
      rainLabel: '${weatherMap['rain'] ?? ''}',
    );
  }
}

class _RecommendationItem {
  const _RecommendationItem({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.rating,
    required this.price,
    required this.duration,
    required this.gallery,
    required this.reason,
  });

  final String icon;
  final String title;
  final String subtitle;
  final String rating;
  final String price;
  final String duration;
  final List<String> gallery;
  final String reason;

  factory _RecommendationItem.fromJson(Map<String, dynamic> json) {
    return _RecommendationItem(
      icon: '${json['icon'] ?? '📍'}',
      title: '${json['title'] ?? ''}',
      subtitle: '${json['subtitle'] ?? ''}',
      rating: '${json['rating'] ?? '★ 4.6'}',
      price: '${json['price'] ?? ''}',
      duration: '${json['duration'] ?? ''}',
      gallery: _Stop._stringList(json['gallery']),
      reason: '${json['reason'] ?? ''}',
    );
  }
}

class _UserProfileData {
  const _UserProfileData({
    required this.name,
    required this.phone,
    required this.preferences,
    required this.modes,
    required this.footprints,
  });

  final String name;
  final String phone;
  final List<Map<String, dynamic>> preferences;
  final List<Map<String, dynamic>> modes;
  final List<String> footprints;

  factory _UserProfileData.fromJson(Map<String, dynamic> json) {
    return _UserProfileData(
      name: '${json['name'] ?? 'Lisa'}',
      phone: '${json['phone'] ?? ''}',
      preferences: _PlanSummary._maps(json['preferences']),
      modes: _PlanSummary._maps(json['modes']),
      footprints: _Stop._stringList(json['footprints']),
    );
  }

  _UserProfileData copyWith({
    String? name,
    String? phone,
    List<Map<String, dynamic>>? preferences,
    List<Map<String, dynamic>>? modes,
    List<String>? footprints,
  }) {
    return _UserProfileData(
      name: name ?? this.name,
      phone: phone ?? this.phone,
      preferences: preferences ?? this.preferences,
      modes: modes ?? this.modes,
      footprints: footprints ?? this.footprints,
    );
  }
}
