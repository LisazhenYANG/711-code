part of '../app_module.dart';

class _Stop {
  const _Stop({
    required this.icon,
    required this.name,
    required this.category,
    required this.time,
    required this.duration,
    required this.transit,
    required this.note,
    this.gallery = const [],
    this.price = '',
    this.hours = '',
    this.booking = '',
    this.lat,
    this.lng,
  });

  final String icon;
  final String name;
  final String category;
  final String time;
  final String duration;
  final String transit;
  final String note;
  final List<String> gallery;
  final String price;
  final String hours;
  final String booking;
  final double? lat;
  final double? lng;

  factory _Stop.fromBackend(Map<String, dynamic> json, {int index = 0}) {
    final images = _stringList(json['imgs']);
    final meta = _stringList(json['meta']);
    final prices = json['prices'];
    final firstPrice =
        prices is List && prices.isNotEmpty && prices.first is List
            ? (prices.first as List).map((item) => '$item').join(' ')
            : '';
    final transitMode = json['transitMode'];
    final transitMin = json['transitMin'];
    final transit = transitMin == null
        ? (index == 0 ? '起点' : '步行 10 分')
        : '${_transitName(transitMode)} $transitMin 分';
    final name = '${json['name'] ?? '未命名地点'}';
    final fallback = _fallbackCoord(name, index);

    return _Stop(
      icon: images.isNotEmpty
          ? images.first
          : _categoryIcon('${json['category'] ?? json['name'] ?? ''}'),
      name: name,
      category: '${json['category'] ?? '地点'}',
      time: '${json['time'] ?? '待定'}',
      duration: '${json['dur'] ?? json['duration'] ?? '约1h'}',
      transit: transit,
      note: meta.isNotEmpty ? meta.join(' · ') : '根据你的需求推荐的路线地点。',
      gallery: images,
      price: firstPrice,
      hours: meta.firstWhere(
        (item) => item.contains('开放') || item.contains('营业'),
        orElse: () => '',
      ),
      booking: firstPrice.isEmpty ? '' : '可查看票券或到店咨询',
      lat: _number(json['lat'] ?? json['latitude']) ?? fallback.$1,
      lng: _number(json['lng'] ?? json['longitude']) ?? fallback.$2,
    );
  }

  Map<String, dynamic> toBackendJson() {
    return {
      'name': name,
      'category': category,
      'time': time,
      'dur': duration,
      'meta': note.isEmpty ? <String>[] : note.split(' · '),
      'imgs': gallery.isEmpty ? [icon] : gallery,
      'prices': price.isEmpty
          ? <List<String>>[]
          : [
              ['普通票', price]
            ],
      'transitMode': _transitModeFromLabel(transit),
      'transitMin': _transitMinutesFromLabel(transit),
      if (lat != null) 'lat': lat,
      if (lng != null) 'lng': lng,
    };
  }

  static List<String> _stringList(Object? value) {
    if (value is! List) return const [];
    return value
        .map((item) => '$item')
        .where((item) => item.isNotEmpty)
        .toList();
  }

  static String _transitName(Object? mode) {
    return switch ('$mode') {
      'metro' => '地铁',
      'taxi' => '打车',
      'bike' => '骑行',
      _ => '步行',
    };
  }

  static String? _transitModeFromLabel(String label) {
    if (label.contains('地铁')) return 'metro';
    if (label.contains('打车')) return 'taxi';
    if (label.contains('公交')) return 'bus';
    if (label.contains('步行')) return 'walk';
    return null;
  }

  static int? _transitMinutesFromLabel(String label) {
    final match = RegExp(r'\d+').firstMatch(label);
    return match == null ? null : int.parse(match.group(0)!);
  }

  static double? _number(Object? value) {
    if (value is num) return value.toDouble();
    if (value is String) return double.tryParse(value);
    return null;
  }

  static (double, double) _fallbackCoord(String name, int index) {
    final known = <String, (double, double)>{
      '梧桐窗边咖啡': (31.2297, 121.4489),
      '静安区图书馆': (31.2322, 121.4437),
      '静雅书局': (31.2305, 121.4468),
      '可纸工坊': (31.2267, 121.4472),
      'UCCA · 当代艺术': (31.2249, 121.4554),
      '慢局桌游社': (31.2275, 121.4523),
    };
    for (final entry in known.entries) {
      if (name.contains(entry.key) || entry.key.contains(name)) {
        return entry.value;
      }
    }
    const defaults = [
      (31.2288, 121.4485),
      (31.2309, 121.4528),
      (31.2265, 121.4561),
      (31.2330, 121.4496),
    ];
    return defaults[index % defaults.length];
  }

  static String _categoryIcon(String text) {
    if (text.contains('咖啡')) return '☕';
    if (text.contains('书') || text.contains('图书')) return '📚';
    if (text.contains('展') || text.contains('艺术')) return '🎨';
    if (text.contains('手')) return '✂️';
    if (text.contains('桌游')) return '🎲';
    return '📍';
  }
}
