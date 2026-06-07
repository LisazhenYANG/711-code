part of '../../app_module.dart';

class _SheetFrame extends StatelessWidget {
  const _SheetFrame({required this.title, required this.child, this.subtitle});

  final String title;
  final String? subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      constraints: const BoxConstraints(maxWidth: 390, maxHeight: 620),
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 18),
      decoration: const BoxDecoration(
        color: _card,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Center(
              child: Container(
                width: 42,
                height: 5,
                decoration: BoxDecoration(
                    color: _border, borderRadius: BorderRadius.circular(99)),
              ),
            ),
            const SizedBox(height: 14),
            Text(title,
                style: const TextStyle(
                    fontSize: 19, fontWeight: FontWeight.w900, color: _ink)),
            if (subtitle != null) ...[
              const SizedBox(height: 4),
              Text(subtitle!,
                  style: const TextStyle(
                      color: _inkSoft,
                      fontSize: 12,
                      fontWeight: FontWeight.w700)),
            ],
            const SizedBox(height: 14),
            child,
          ],
        ),
      ),
    );
  }
}

class _PlusSheet extends StatelessWidget {
  const _PlusSheet({required this.onGo, required this.onClose});

  final ValueChanged<ScreenStage> onGo;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    return _SheetFrame(
      title: '选择规划方式',
      child: Column(
        children: [
          _PlusOptionCard(
            icon: '🤖',
            sparkle: '✨',
            title: '我帮你规划',
            sub: '回答几个简单问题，AI 帮你搭一条专属路线',
            steps: const ['📍 地点', '⏰ 时间', '🎯 偏好'],
            highlighted: true,
            onTap: () => onGo(ScreenStage.mood),
          ),
          const SizedBox(height: 12),
          _PlusOptionCard(
            icon: '✍️',
            title: '自主规划',
            sub: '自由提问，想问什么都可以',
            steps: const ['💬 自由对话'],
            onTap: () => onGo(ScreenStage.freeChat),
          ),
        ],
      ),
    );
  }
}

class _PlusOptionCard extends StatelessWidget {
  const _PlusOptionCard({
    required this.icon,
    required this.title,
    required this.sub,
    required this.steps,
    required this.onTap,
    this.sparkle,
    this.highlighted = false,
  });

  final String icon;
  final String? sparkle;
  final String title;
  final String sub;
  final List<String> steps;
  final VoidCallback onTap;
  final bool highlighted;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: highlighted ? const Color(0xFFFFFAF6) : _card2,
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: highlighted ? _brown : _border, width: 1.5),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFFA05A32).withValues(alpha: .08),
              blurRadius: 16,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Stack(
              clipBehavior: Clip.none,
              children: [
                Container(
                  width: 58,
                  height: 58,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: highlighted ? const Color(0xFFFFE9DF) : Colors.white,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(icon, style: const TextStyle(fontSize: 30)),
                ),
                if (sparkle != null)
                  Positioned(
                    right: -6,
                    top: -6,
                    child: Text(sparkle!, style: const TextStyle(fontSize: 18)),
                  ),
              ],
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: const TextStyle(
                          color: _ink,
                          fontSize: 17,
                          fontWeight: FontWeight.w900)),
                  const SizedBox(height: 4),
                  Text(sub,
                      style: const TextStyle(
                          color: _inkSoft,
                          fontSize: 12,
                          height: 1.35,
                          fontWeight: FontWeight.w700)),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: steps.map((step) => _TinyTag(step)).toList(),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _VenueSheet extends StatelessWidget {
  const _VenueSheet({
    required this.recommendations,
    required this.onClose,
    required this.onShowOverlay,
  });

  final List<_RecommendationItem> recommendations;
  final VoidCallback onClose;
  final ValueChanged<_AppOverlay> onShowOverlay;

  @override
  Widget build(BuildContext context) {
    return _SheetFrame(
      title: '为你精选的推荐',
      subtitle: '点圈选好，点行看详情',
      child: Column(
        children: [
          for (final item in recommendations)
            _SheetAction(
              icon: item.icon,
              title: item.title,
              sub: item.subtitle,
              onTap: () => onShowOverlay(_AppOverlay.venueDetail),
            ),
          if (recommendations.isEmpty)
            const Text('正在获取推荐…',
                style: TextStyle(color: _inkSoft, fontWeight: FontWeight.w700)),
          const SizedBox(height: 10),
          _PrimaryButton(label: '选好了，规划路线 →', onTap: onClose),
        ],
      ),
    );
  }
}

class _VenueDetailSheet extends StatelessWidget {
  const _VenueDetailSheet(
      {required this.recommendation, required this.onClose});

  final _RecommendationItem? recommendation;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    return _SheetFrame(
      title: recommendation?.title ?? '推荐地点',
      subtitle:
          '${recommendation?.rating ?? '★ 4.6'} · ${recommendation?.price ?? ''} · ${recommendation?.duration ?? ''}',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
              height: 96,
              decoration: BoxDecoration(
                  color: _card2, borderRadius: BorderRadius.circular(18)),
              alignment: Alignment.center,
              child: Text(
                  (recommendation?.gallery.isEmpty ?? true)
                      ? (recommendation?.icon ?? '📍')
                      : recommendation!.gallery.join(' '),
                  style: const TextStyle(fontSize: 36))),
          const SizedBox(height: 12),
          const Text('AI 推荐理由', style: TextStyle(fontWeight: FontWeight.w900)),
          const SizedBox(height: 6),
          Text(recommendation?.reason ?? '根据当前位置和路线顺序推荐，可以加入路线继续规划。',
              style: TextStyle(
                  color: _inkMid, height: 1.45, fontWeight: FontWeight.w700)),
          const SizedBox(height: 14),
          _PrimaryButton(label: '加入路线', onTap: onClose),
        ],
      ),
    );
  }
}

class _AddPlaceSheet extends StatefulWidget {
  const _AddPlaceSheet({
    required this.loadRecommendations,
    required this.onAdd,
    required this.onAddCustom,
    required this.onClose,
  });

  final Future<List<_RecommendationItem>> Function() loadRecommendations;
  final ValueChanged<String> onAdd;
  final ValueChanged<String> onAddCustom;
  final VoidCallback onClose;

  @override
  State<_AddPlaceSheet> createState() => _AddPlaceSheetState();
}

class _AddPlaceSheetState extends State<_AddPlaceSheet> {
  final controller = TextEditingController();
  late Future<List<_RecommendationItem>> _recommendationsFuture;

  @override
  void initState() {
    super.initState();
    _recommendationsFuture = widget.loadRecommendations();
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return _SheetFrame(
      title: '添加地点',
      subtitle: '可以自己添加，也可以从推荐里选择',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          TextField(
            controller: controller,
            textInputAction: TextInputAction.done,
            decoration: InputDecoration(
              hintText: '输入地点名，例如：武康路、某家咖啡店',
              filled: true,
              fillColor: Colors.white,
              contentPadding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
                borderSide: const BorderSide(color: _border),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
                borderSide: const BorderSide(color: _border),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
                borderSide: const BorderSide(color: _brown, width: 1.4),
              ),
            ),
            onSubmitted: (_) => _submitCustom(),
          ),
          const SizedBox(height: 10),
          _PrimaryButton(label: '添加这个地点', onTap: _submitCustom),
          const SizedBox(height: 12),
          const Text('推荐地点',
              style: TextStyle(fontWeight: FontWeight.w900, color: _ink)),
          const SizedBox(height: 8),
          FutureBuilder<List<_RecommendationItem>>(
            future: _recommendationsFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Padding(
                  padding: EdgeInsets.symmetric(vertical: 16),
                  child: Center(child: CircularProgressIndicator()),
                );
              }
              if (snapshot.hasError) {
                return const Text(
                  '附近推荐暂时加载失败，可以先手动添加。',
                  style: TextStyle(color: _inkSoft, fontWeight: FontWeight.w700),
                );
              }
              final recommendations =
                  snapshot.data ?? const <_RecommendationItem>[];
              if (recommendations.isEmpty) {
                return const Text('暂无推荐地点，可以先手动添加。',
                    style:
                        TextStyle(color: _inkSoft, fontWeight: FontWeight.w700));
              }
              return Column(
                children: [
                  for (final item in recommendations)
                    _SheetAction(
                      icon: item.icon,
                      title: item.title,
                      sub: item.subtitle,
                      onTap: () => widget.onAdd(item.title),
                    ),
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  void _submitCustom() {
    final name = controller.text.trim();
    if (name.isEmpty) return;
    widget.onAddCustom(name);
  }
}

class _MealSheet extends StatefulWidget {
  const _MealSheet({
    required this.loadRestaurants,
    required this.onAddMeal,
    required this.onClose,
  });

  final Future<List<_MealRestaurant>> Function(String slot) loadRestaurants;
  final ValueChanged<String> onAddMeal;
  final VoidCallback onClose;

  @override
  State<_MealSheet> createState() => _MealSheetState();
}

class _MealSheetState extends State<_MealSheet> {
  String selectedSlot = 'lunch';
  late Future<List<_MealRestaurant>> _restaurantsFuture;

  static const slots = [
    _MealSlot('lunch', '🍜', '中饭', '12:00-13:30'),
    _MealSlot('dinner', '🍽️', '晚饭', '18:00-19:30'),
  ];

  @override
  void initState() {
    super.initState();
    _restaurantsFuture = widget.loadRestaurants(selectedSlot);
  }

  void _changeSlot(String slot) {
    setState(() {
      selectedSlot = slot;
      _restaurantsFuture = widget.loadRestaurants(selectedSlot);
    });
  }

  @override
  Widget build(BuildContext context) {
    final slot = slots.firstWhere((item) => item.key == selectedSlot);
    return _SheetFrame(
      title: '安排吃饭',
      subtitle: '先选时间段，再选择推荐餐厅加入路线',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              for (final item in slots) ...[
                Expanded(
                  child: GestureDetector(
                    onTap: () => _changeSlot(item.key),
                    child: _MealSlotButton(
                      slot: item,
                      selected: selectedSlot == item.key,
                    ),
                  ),
                ),
                if (item != slots.last) const SizedBox(width: 8),
              ],
            ],
          ),
          const SizedBox(height: 12),
          Text('${slot.name}推荐餐厅',
              style: const TextStyle(fontWeight: FontWeight.w900, color: _ink)),
          const SizedBox(height: 8),
          FutureBuilder<List<_MealRestaurant>>(
            future: _restaurantsFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Padding(
                  padding: EdgeInsets.symmetric(vertical: 16),
                  child: Center(child: CircularProgressIndicator()),
                );
              }
              if (snapshot.hasError) {
                return const Padding(
                  padding: EdgeInsets.symmetric(vertical: 12),
                  child: Text(
                    '附近餐厅暂时加载失败，请稍后再试。',
                    style: TextStyle(color: _inkSoft, fontWeight: FontWeight.w700),
                  ),
                );
              }
              final meals = snapshot.data ?? const <_MealRestaurant>[];
              if (meals.isEmpty) {
                return const Padding(
                  padding: EdgeInsets.symmetric(vertical: 12),
                  child: Text(
                    '附近暂时没有合适餐厅。',
                    style: TextStyle(color: _inkSoft, fontWeight: FontWeight.w700),
                  ),
                );
              }
              return Column(
                children: [
                  for (final meal in meals)
                    _SheetAction(
                      icon: meal.icon,
                      title: meal.name,
                      sub: meal.subtitle,
                      onTap: () => widget.onAddMeal('$selectedSlot|${meal.name}'),
                    ),
                ],
              );
            },
          ),
        ],
      ),
    );
  }
}

class _MealSlot {
  const _MealSlot(this.key, this.icon, this.name, this.time);

  final String key;
  final String icon;
  final String name;
  final String time;
}

class _MealSlotButton extends StatelessWidget {
  const _MealSlotButton({required this.slot, required this.selected});

  final _MealSlot slot;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
      decoration: BoxDecoration(
        color: selected ? _brown : _card2,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: selected ? _brown : _border),
      ),
      child: Column(
        children: [
          Text(slot.icon, style: const TextStyle(fontSize: 20)),
          const SizedBox(height: 4),
          Text(slot.name,
              style: TextStyle(
                  color: selected ? Colors.white : _ink,
                  fontWeight: FontWeight.w900)),
          const SizedBox(height: 2),
          Text(slot.time,
              style: TextStyle(
                  color: selected ? Colors.white70 : _inkSoft,
                  fontSize: 11,
                  fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

class _TransitSheet extends StatelessWidget {
  const _TransitSheet({required this.onSelect, required this.onClose});

  final ValueChanged<String> onSelect;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    return _SheetFrame(
      title: '选择交通方式',
      child: Column(
        children: [
          _SheetAction(
              icon: '🚶',
              title: '步行',
              sub: '约 10 分钟',
              onTap: () => onSelect('walk')),
          _SheetAction(
              icon: '🚇',
              title: '地铁',
              sub: '约 15 分钟',
              onTap: () => onSelect('metro')),
          _SheetAction(
              icon: '🚗',
              title: '打车',
              sub: '约 8 分钟',
              onTap: () => onSelect('taxi')),
          _SheetAction(
              icon: '🚌',
              title: '公交',
              sub: '约 20 分钟',
              onTap: () => onSelect('bus')),
        ],
      ),
    );
  }
}

class _SpotSheet extends StatelessWidget {
  const _SpotSheet({required this.stop, required this.onClose});

  final _Stop stop;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    final detail = _SpotDetail.fromStop(stop);

    return _SheetFrame(
      title: stop.name,
      subtitle: '${stop.category} · ${detail.rating} · ${detail.price}',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            height: 136,
            decoration: BoxDecoration(
              gradient: LinearGradient(colors: detail.colors),
              borderRadius: BorderRadius.circular(18),
            ),
            alignment: Alignment.center,
            child:
                Text(detail.photoEmoji, style: const TextStyle(fontSize: 46)),
          ),
          const SizedBox(height: 12),
          const Text('地点介绍', style: TextStyle(fontWeight: FontWeight.w900)),
          const SizedBox(height: 6),
          Text(detail.intro,
              style: const TextStyle(
                  color: _inkMid, height: 1.45, fontWeight: FontWeight.w700)),
          const SizedBox(height: 12),
          _SpotInfoRow(label: '营业时间', value: detail.hours),
          _SpotInfoRow(label: '地址', value: detail.address),
          _SpotInfoRow(label: '预约', value: detail.booking),
          _SpotInfoRow(label: '适合', value: detail.bestFor),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: detail.tags.map((tag) => _TinyTag(tag)).toList(),
          ),
          const SizedBox(height: 14),
          _PrimaryButton(label: '知道了', onTap: onClose),
        ],
      ),
    );
  }
}

class _SpotInfoRow extends StatelessWidget {
  const _SpotInfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 68,
            child: Text(label,
                style: const TextStyle(
                    color: _inkSoft,
                    fontSize: 12,
                    fontWeight: FontWeight.w800)),
          ),
          Expanded(
            child: Text(value,
                style: const TextStyle(
                    color: _ink, fontSize: 13, fontWeight: FontWeight.w800)),
          ),
        ],
      ),
    );
  }
}

class _SpotDetail {
  const _SpotDetail({
    required this.photoEmoji,
    required this.colors,
    required this.rating,
    required this.price,
    required this.intro,
    required this.hours,
    required this.address,
    required this.booking,
    required this.bestFor,
    required this.tags,
  });

  final String photoEmoji;
  final List<Color> colors;
  final String rating;
  final String price;
  final String intro;
  final String hours;
  final String address;
  final String booking;
  final String bestFor;
  final List<String> tags;

  factory _SpotDetail.fromStop(_Stop stop) {
    final local = switch (stop.name) {
      '可纸工坊' => const _SpotDetail(
          photoEmoji: '✂️ 🧵 📦',
          colors: [Color(0xFFFFE1D7), Color(0xFFF7E7C8)],
          rating: '★ 4.8',
          price: '¥128/人起',
          intro: '安静的纸艺手作空间，适合用一两个小时做一个小作品。店内节奏比较慢，老师会带着做，适合作为一日路线的第一站。',
          hours: '10:00 - 20:00',
          address: '静安区南京西路附近',
          booking: '建议提前预约体验场次',
          bestFor: '手作体验、安静开场、慢节奏',
          tags: ['手作', '需预约', '安静', '体验感'],
        ),
      'UCCA · 当代艺术' => const _SpotDetail(
          photoEmoji: '🎨 🖼️ ✨',
          colors: [Color(0xFFDDEAFF), Color(0xFFF0ECFF)],
          rating: '★ 4.7',
          price: '¥88/人起',
          intro: '小而精的当代艺术展览空间，展陈节奏轻松，适合慢慢看、拍照和聊天。工作日下午人流更友好。',
          hours: '10:00 - 18:00，周一闭馆',
          address: '静安区文艺街区内',
          booking: '热门展建议提前购票',
          bestFor: '看展、拍照、轻文化体验',
          tags: ['展览', '可购票', '出片', '室内'],
        ),
      '静雅书局' => const _SpotDetail(
          photoEmoji: '📚 ☕ 🪟',
          colors: [Color(0xFFE1F3E8), Color(0xFFFFF0C9)],
          rating: '★ 4.6',
          price: '¥35/人起',
          intro: '带咖啡座的安静书店，窗边座位适合休息和收尾。这里时间弹性大，适合把当天的节奏慢慢放下来。',
          hours: '09:30 - 21:30',
          address: '静安区苏河湾附近',
          booking: '无需预约',
          bestFor: '休息、阅读、咖啡、路线收尾',
          tags: ['书店', '咖啡', '无需预约', '放松'],
        ),
      _ => _SpotDetail(
          photoEmoji:
              stop.gallery.isEmpty ? '${stop.icon} 📍' : stop.gallery.join(' '),
          colors: const [Color(0xFFFFF5F0), Color(0xFFF0ECFF)],
          rating: '★ 4.6',
          price: stop.price.isEmpty ? '详见商家' : stop.price,
          intro: stop.note,
          hours: stop.hours.isEmpty ? '以商家当日营业时间为准' : stop.hours,
          address: '上海市静安区',
          booking: stop.booking.isEmpty ? '视具体项目而定' : stop.booking,
          bestFor: stop.category,
          tags: [stop.category, stop.duration],
        ),
    };
    return _SpotDetail(
      photoEmoji:
          stop.gallery.isEmpty ? local.photoEmoji : stop.gallery.join(' '),
      colors: local.colors,
      rating: local.rating,
      price: stop.price.isEmpty ? local.price : stop.price,
      intro: stop.note.isEmpty ? local.intro : stop.note,
      hours: stop.hours.isEmpty ? local.hours : stop.hours,
      address: local.address,
      booking: stop.booking.isEmpty ? local.booking : stop.booking,
      bestFor: local.bestFor,
      tags: local.tags,
    );
  }
}

class _RecDetailSheet extends StatelessWidget {
  const _RecDetailSheet({required this.recommendation, required this.onClose});

  final _RecommendationItem? recommendation;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    return _VenueDetailSheet(recommendation: recommendation, onClose: onClose);
  }
}

class _LockInfoSheet extends StatelessWidget {
  const _LockInfoSheet({required this.onClose, required this.onRestoreStops});

  final VoidCallback onClose;
  final VoidCallback onRestoreStops;

  @override
  Widget build(BuildContext context) {
    return _SheetFrame(
      title: '🔒 锁定这个景点',
      subtitle: '锁定后，AI 重新排行程时也不会动它。',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _TinyTag('票已经买好，时间定死了'),
          const SizedBox(height: 8),
          const _TinyTag('这个地方非去不可'),
          const SizedBox(height: 8),
          const _TinyTag('这个地方作为集合点'),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                  child: _SmallButton(label: '还原站点', onTap: onRestoreStops)),
              const SizedBox(width: 8),
              Expanded(child: _SmallButton(label: '知道了', onTap: onClose)),
            ],
          ),
        ],
      ),
    );
  }
}

class _PaymentSheet extends StatelessWidget {
  const _PaymentSheet({
    required this.bookings,
    required this.onClose,
    required this.onComplete,
  });

  final List<_BookingItem> bookings;
  final VoidCallback onClose;
  final Future<void> Function() onComplete;

  @override
  Widget build(BuildContext context) {
    final pending = bookings.where((item) => !item.done).toList();
    final total = pending.isEmpty ? bookings : pending;
    return _SheetFrame(
      title: '确认支付',
      subtitle: total.isEmpty ? '暂无待处理项目' : '${total.length} 个预约/购票项目',
      child: Column(
        children: [
          for (final booking in total)
            _BookingRow(
              icon: booking.icon,
              title: booking.name,
              sub: booking.subtitle,
              status: booking.statusText,
            ),
          _PreferenceRow(label: '商品数量', value: '${total.length} 项'),
          const _PreferenceRow(label: '服务费', value: '免费'),
          const Divider(color: _border),
          _PreferenceRow(label: '合计', value: _paymentTotal(total)),
          const SizedBox(height: 12),
          _PrimaryButton(label: '确认支付 →', onTap: onComplete),
          const SizedBox(height: 8),
          _SmallButton(label: '取消', onTap: onClose),
        ],
      ),
    );
  }

  String _paymentTotal(List<_BookingItem> items) {
    var sum = 0;
    for (final item in items) {
      final match = RegExp(r'\d+').firstMatch(item.price);
      if (match != null) sum += int.parse(match.group(0)!);
    }
    return sum == 0 ? '到店确认' : '¥$sum';
  }
}

class _LocationSheet extends StatelessWidget {
  const _LocationSheet({
    required this.stop,
    required this.currentLat,
    required this.currentLng,
    required this.onClose,
  });

  final _Stop stop;
  final double? currentLat;
  final double? currentLng;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    final distanceKm = _distanceKm(currentLat, currentLng, stop.lat, stop.lng);
    final walkMinutes = _travelMinutes(distanceKm, speedKmh: 4.5);
    final metroMinutes = _travelMinutes(distanceKm, speedKmh: 22, padding: 8);
    final taxiMinutes = _travelMinutes(distanceKm, speedKmh: 28, padding: 4);
    final busMinutes = _travelMinutes(distanceKm, speedKmh: 16, padding: 10);
    final subtitle = distanceKm == null
        ? '开启定位后可查看前往 ${stop.name} 的方式'
        : '前往 ${stop.name} · 约 ${(distanceKm * 1000).round()}m';

    return _SheetFrame(
      title: '怎么前往',
      subtitle: subtitle,
      child: Column(
        children: [
          _SheetAction(
            icon: '🚶',
            title: '步行',
            sub: walkMinutes == null ? '需要定位后计算' : '约 $walkMinutes 分钟',
            onTap: () => _openRoute('walk'),
          ),
          _SheetAction(
            icon: '🚇',
            title: '地铁',
            sub: metroMinutes == null ? '需要定位后计算' : '约 $metroMinutes 分钟',
            onTap: () => _openRoute('metro'),
          ),
          _SheetAction(
            icon: '🚗',
            title: '打车',
            sub: taxiMinutes == null ? '需要定位后计算' : '约 $taxiMinutes 分钟',
            onTap: () => _openRoute('car'),
          ),
          _SheetAction(
            icon: '🚌',
            title: '公交',
            sub: busMinutes == null ? '需要定位后计算' : '约 $busMinutes 分钟',
            onTap: () => _openRoute('bus'),
          ),
          const SizedBox(height: 14),
          _PrimaryButton(label: '知道了', onTap: onClose),
        ],
      ),
    );
  }

  void _openRoute(String mode) {
    if (currentLat == null ||
        currentLng == null ||
        stop.lat == null ||
        stop.lng == null) {
      onClose();
      return;
    }
    final from = '${currentLng!.toStringAsFixed(6)},${currentLat!.toStringAsFixed(6)},我的位置';
    final to = '${stop.lng!.toStringAsFixed(6)},${stop.lat!.toStringAsFixed(6)},${stop.name}';
    final uri = Uri.https('uri.amap.com', '/navigation', {
      'from': from,
      'to': to,
      'mode': mode,
      'policy': '1',
      'src': 'manyou',
      'coordinate': 'gaode',
      'callnative': '1',
    });
    openExternalUrl(uri.toString());
    onClose();
  }
}

int? _travelMinutes(double? distanceKm, {required double speedKmh, int padding = 0}) {
  if (distanceKm == null) return null;
  return math.max(1, ((distanceKm / speedKmh) * 60).round() + padding);
}

class _HeartSheet extends StatelessWidget {
  const _HeartSheet({required this.onChoose, required this.onClose});

  final ValueChanged<String> onChoose;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    return _SheetFrame(
      title: '🌧️ 心动提醒',
      subtitle: '附近可能下小雨，建议带伞或把户外点换成室内。',
      child: Row(
        children: [
          Expanded(
              child:
                  _SmallButton(label: '忽略', onTap: () => onChoose('ignore'))),
          const SizedBox(width: 8),
          Expanded(
              child:
                  _SmallButton(label: '换一下', onTap: () => onChoose('change'))),
        ],
      ),
    );
  }
}

class _SheetAction extends StatelessWidget {
  const _SheetAction({
    required this.icon,
    required this.title,
    required this.sub,
    required this.onTap,
  });

  final String icon;
  final String title;
  final String sub;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
            color: _card2, borderRadius: BorderRadius.circular(18)),
        child: Row(
          children: [
            Text(icon, style: const TextStyle(fontSize: 28)),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: const TextStyle(fontWeight: FontWeight.w900)),
                  Text(sub,
                      style: const TextStyle(
                          color: _inkSoft,
                          fontSize: 12,
                          fontWeight: FontWeight.w700)),
                ],
              ),
            ),
            const Text('›',
                style: TextStyle(
                    fontSize: 24,
                    color: _inkSoft,
                    fontWeight: FontWeight.w900)),
          ],
        ),
      ),
    );
  }
}
