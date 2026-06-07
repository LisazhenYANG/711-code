part of '../../app_module.dart';

class _HomeScreen extends StatelessWidget {
  const _HomeScreen({
    required this.activePlan,
    required this.plan,
    required this.stops,
    required this.weather,
    required this.onGo,
    required this.onShowOverlay,
  });

  final bool activePlan;
  final _PlanSummary? plan;
  final List<_Stop> stops;
  final _WeatherSummary? weather;
  final ValueChanged<ScreenStage> onGo;
  final ValueChanged<_AppOverlay> onShowOverlay;

  @override
  Widget build(BuildContext context) {
    return _ScreenScroll(
      key: const ValueKey('home'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _HomeHeader(weather: weather),
          const SizedBox(height: 18),
          _SectionHead(title: '我的计划', count: activePlan ? '1个计划' : '0个计划'),
          const SizedBox(height: 10),
          if (activePlan)
            _PlanCard(
              plan: plan,
              stops: stops,
              onTap: () => onGo(ScreenStage.route),
              onTicket: () => onGo(ScreenStage.ticket),
            )
          else
            _EmptyPlan(onStart: () => onShowOverlay(_AppOverlay.plus)),
          const SizedBox(height: 100),
        ],
      ),
    );
  }
}

class _HistoryMiniCard extends StatelessWidget {
  const _HistoryMiniCard({
    required this.title,
    required this.icons,
    required this.count,
    required this.onTap,
  });

  final String title;
  final String icons;
  final int count;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: _ClayCard(
        child: Row(
          children: [
            Text(icons, style: const TextStyle(fontSize: 30)),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: const TextStyle(fontWeight: FontWeight.w900)),
                  const SizedBox(height: 4),
                  Text('已完成 · 上海 · $count个地点',
                      style: const TextStyle(
                          color: _inkSoft,
                          fontSize: 12,
                          fontWeight: FontWeight.w700)),
                ],
              ),
            ),
            const _StatusBadge(label: '已完成', color: _metro),
          ],
        ),
      ),
    );
  }
}

class _HomeHeader extends StatelessWidget {
  const _HomeHeader({this.weather});

  final _WeatherSummary? weather;

  @override
  Widget build(BuildContext context) {
    final summary = weather;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Text(_weatherIcon(summary?.conditionLabel), style: const TextStyle(fontSize: 24)),
                const SizedBox(width: 6),
                Text(summary?.temperatureLabel ?? '--',
                    style:
                        const TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
                const SizedBox(width: 6),
                Text(summary?.conditionLabel ?? '天气良好',
                    style:
                        const TextStyle(color: _inkMid, fontWeight: FontWeight.w700)),
              ],
            ),
            _SoftPill(label: '📍 ${summary?.locationLabel ?? '上海·静安区'}'),
          ],
        ),
        const SizedBox(height: 8),
        Text(
          [
            summary?.dateLabel ?? '今天',
            if ((summary?.rainLabel ?? '').isNotEmpty) '降雨 ${summary!.rainLabel}',
          ].join(' · '),
          style: const TextStyle(color: _inkSoft, fontWeight: FontWeight.w700),
        ),
      ],
    );
  }
}

String _weatherIcon(String? condition) {
  final text = condition ?? '';
  if (text.contains('雨')) return '🌧️';
  if (text.contains('晴')) return '☀️';
  if (text.contains('云')) return '☁️';
  return '🌤️';
}

class _EmptyPlan extends StatelessWidget {
  const _EmptyPlan({required this.onStart});

  final VoidCallback onStart;

  @override
  Widget build(BuildContext context) {
    return _ClayCard(
      padding: const EdgeInsets.fromLTRB(18, 28, 18, 22),
      child: Column(
        children: [
          Container(
            width: 88,
            height: 88,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              color: Color(0xFFF0ECFF),
            ),
            alignment: Alignment.center,
            child: const Text('🗺️', style: TextStyle(fontSize: 42)),
          ),
          const SizedBox(height: 14),
          const Text('还没有计划',
              style: TextStyle(
                  fontSize: 22, fontWeight: FontWeight.w900, color: _ink)),
          const SizedBox(height: 5),
          const Text('点击下方 + 开始探索你的第一条路线',
              style: TextStyle(color: _inkSoft, fontSize: 13)),
          const SizedBox(height: 18),
          _PrimaryButton(label: '开始规划 ✨', onTap: onStart),
        ],
      ),
    );
  }
}

class _PlanCard extends StatelessWidget {
  const _PlanCard({
    required this.onTap,
    this.plan,
    this.stops = _stops,
    this.onTicket,
  });

  final VoidCallback onTap;
  final _PlanSummary? plan;
  final List<_Stop> stops;
  final VoidCallback? onTicket;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: _ClayCard(
        padding: EdgeInsets.zero,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              height: 112,
              decoration: const BoxDecoration(
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                gradient: LinearGradient(
                    colors: [Color(0xFFFFD6C9), Color(0xFFF0ECFF)]),
              ),
              alignment: Alignment.center,
              child: Text(
                stops.take(3).map((stop) => stop.icon).join(' '),
                style: const TextStyle(fontSize: 42),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(plan?.title ?? '静安慢悠悠之旅',
                            style: TextStyle(
                                fontSize: 20, fontWeight: FontWeight.w900)),
                      ),
                      _StatusBadge(label: plan?.status ?? '进行中', color: _green),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 6,
                    children: [
                      _TinyTag(plan?.duration ?? '半天'),
                      const _TinyTag('·'),
                      _TinyTag('${stops.length}个地点'),
                    ],
                  ),
                  const SizedBox(height: 12),
                  for (final todo in (plan?.todos ??
                      const [
                        {'done': true, 'label': '预约 UCCA 展览票'},
                        {'done': false, 'label': '带充电宝和雨伞'},
                      ]))
                    _TodoLine(
                      done: todo['done'] == true,
                      label: '${todo['label'] ?? ''}',
                    ),
                  if (onTicket != null) ...[
                    const SizedBox(height: 12),
                    GestureDetector(
                      onTap: () {
                        onTicket!();
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 10),
                        decoration: BoxDecoration(
                          color: _card2,
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Row(
                          children: const [
                            Text('🎫', style: TextStyle(fontSize: 20)),
                            SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                '查看票券与预约',
                                style: TextStyle(
                                    fontWeight: FontWeight.w900, color: _ink),
                              ),
                            ),
                            Text('›',
                                style: TextStyle(
                                    fontSize: 22,
                                    color: _inkSoft,
                                    fontWeight: FontWeight.w900)),
                          ],
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
