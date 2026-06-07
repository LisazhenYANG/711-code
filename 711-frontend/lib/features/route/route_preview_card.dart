part of '../../app_module.dart';

class _RoutePreviewCard extends StatelessWidget {
  const _RoutePreviewCard({this.stops = _stops, required this.onConfirm});

  final List<_Stop> stops;
  final VoidCallback onConfirm;

  @override
  Widget build(BuildContext context) {
    return _ClayCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Expanded(
                  child: Text('推荐路线 ★★',
                      style: TextStyle(
                          fontSize: 18, fontWeight: FontWeight.w900))),
              Text('🚶 1.3km · 2.5h',
                  style: TextStyle(
                      color: _inkMid,
                      fontSize: 12,
                      fontWeight: FontWeight.w800)),
            ],
          ),
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
          _PrimaryButton(label: '确认这条路线 →', onTap: onConfirm),
        ],
      ),
    );
  }
}
