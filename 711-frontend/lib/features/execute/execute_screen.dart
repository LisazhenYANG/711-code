part of '../../app_module.dart';

class _ExecuteScreen extends StatelessWidget {
  const _ExecuteScreen({
    required this.paid,
    required this.bookings,
    required this.selectedBookingIndexes,
    required this.packingList,
    required this.weather,
    required this.onGo,
    required this.onShowOverlay,
    required this.onToggleBookingSelection,
  });

  final bool paid;
  final List<_BookingItem> bookings;
  final Set<int> selectedBookingIndexes;
  final List<String> packingList;
  final _WeatherSummary? weather;
  final ValueChanged<ScreenStage> onGo;
  final ValueChanged<_AppOverlay> onShowOverlay;
  final ValueChanged<int> onToggleBookingSelection;

  @override
  Widget build(BuildContext context) {
    return _ScreenScroll(
      key: const ValueKey('execute'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _TopBack(label: '', onTap: () => onGo(ScreenStage.route)),
              const SizedBox(width: 8),
              const Text('出发前确认',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
            ],
          ),
          const SizedBox(height: 14),
          _ClayCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('📋 预约清单',
                    style:
                        TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
                const SizedBox(height: 12),
                for (var i = 0; i < bookings.length; i++)
                  GestureDetector(
                    onTap: bookings[i].done
                        ? null
                        : () => onShowOverlay(_AppOverlay.payment),
                    child: _BookingRow(
                      icon: bookings[i].icon,
                      title: bookings[i].name,
                      sub: bookings[i].subtitle,
                      status: bookings[i].done ? bookings[i].statusText : '待处理',
                      done: bookings[i].done,
                      selectable: !bookings[i].done,
                      selected: selectedBookingIndexes.contains(i),
                      onToggle: () => onToggleBookingSelection(i),
                    ),
                  ),
                if (bookings.isEmpty)
                  const Text('当前路线暂无需要预约或购票的项目',
                      style: TextStyle(
                          color: _inkSoft, fontWeight: FontWeight.w700)),
              ],
            ),
          ),
          const SizedBox(height: 14),
          _ClayCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('🎒 需要带的东西',
                    style:
                        TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final item in (packingList.isEmpty
                        ? const ['预约二维码', '充电宝', '轻便鞋', '小伞']
                        : packingList))
                      _TinyTag('✓ $item'),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          _ClayCard(
            color: const Color(0xFFFFF9E9),
            child: Row(
              children: [
                Text(_weatherIcon(weather?.conditionLabel),
                    style: const TextStyle(fontSize: 34)),
                SizedBox(width: 12),
                Expanded(
                  child: Text(
                    '当前天气 ${weather?.conditionLabel ?? '稳定'}${(weather?.temperatureLabel ?? '').isNotEmpty ? '，${weather!.temperatureLabel}' : ''}。心动模式已开启：如果天气突变或餐厅排队太久，会提醒你换一个更轻松的选择。',
                    style: const TextStyle(
                        color: _inkMid,
                        height: 1.45,
                        fontWeight: FontWeight.w700),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 18),
          if (paid)
            _ClayCard(
              color: const Color(0xFFEFFAF3),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('📋 购票与预约结果',
                      style: TextStyle(fontWeight: FontWeight.w900)),
                  const SizedBox(height: 8),
                  for (final booking in bookings.where((item) => item.done))
                    _TodoLine(
                      done: true,
                      label:
                          '${booking.name} · ${booking.statusText} · ${booking.code.isEmpty ? '已确认' : booking.code}',
                    ),
                ],
              ),
            ),
          if (paid) const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: GestureDetector(
                  onTap: paid
                      ? () => onGo(ScreenStage.guide)
                      : () => onShowOverlay(_AppOverlay.payment),
                  child: Container(
                    height: 56,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: _brown,
                      borderRadius: BorderRadius.circular(28),
                      boxShadow: [
                        BoxShadow(
                          color: _brown.withValues(alpha: .28),
                          blurRadius: 18,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: Text(
                      paid ? '开始出发 →' : '处理预约与购票 →',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: GestureDetector(
                  onTap: () => onGo(ScreenStage.guide),
                  child: Container(
                    height: 56,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: const Color(0xFFE9A28D),
                      borderRadius: BorderRadius.circular(28),
                    ),
                    child: const Text(
                      '先跳过，直接出发',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 15,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 100),
        ],
      ),
    );
  }
}
