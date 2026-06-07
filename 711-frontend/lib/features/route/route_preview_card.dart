part of '../../app_module.dart';

class _RoutePreviewCard extends StatelessWidget {
  const _RoutePreviewCard({
    this.title = '推荐路线',
    this.subtitle = '',
    this.metricLabel = '🚶 1.3km · 2.5h',
    this.overloadHint = '',
    this.confirmLabel = '确认这条路线 →',
    this.selected = false,
    this.stops = _stops,
    required this.onConfirm,
  });

  final String title;
  final String subtitle;
  final String metricLabel;
  final String overloadHint;
  final String confirmLabel;
  final bool selected;
  final List<_Stop> stops;
  final VoidCallback onConfirm;

  @override
  Widget build(BuildContext context) {
    return _ClayCard(
      border: selected ? _brown : null,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                  child: Text(title,
                      style: TextStyle(
                          fontSize: 18, fontWeight: FontWeight.w900))),
              Text(metricLabel,
                  style: const TextStyle(
                      color: _inkMid,
                      fontSize: 12,
                      fontWeight: FontWeight.w800)),
            ],
          ),
          if (subtitle.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(
              subtitle,
              style: const TextStyle(
                color: _inkSoft,
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
          if (overloadHint.isNotEmpty) ...[
            const SizedBox(height: 8),
            _SoftPill(label: '行程节奏：$overloadHint'),
          ],
          const SizedBox(height: 14),
          ...List.generate(stops.length, (i) {
            final s = stops[i];
            return Column(
              children: [
                _RouteLineItem(index: i, stop: s),
                if (i < stops.length - 1)
                  Padding(
                    padding: const EdgeInsets.only(left: 44, top: 4, bottom: 4),
                    child: Align(
                      alignment: Alignment.centerLeft,
                      child: _TransitPill(
                          label: i == 0 ? '🚶 步行 10 分' : '🚇 地铁 15 分',
                          blue: i == 1),
                    ),
                  ),
              ],
            );
          }),
          const SizedBox(height: 14),
          _PrimaryButton(label: confirmLabel, onTap: onConfirm),
        ],
      ),
    );
  }
}
