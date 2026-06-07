part of '../../app_module.dart';

class _RouteLineItem extends StatelessWidget {
  const _RouteLineItem({required this.index, required this.stop});

  final int index;
  final _Stop stop;

  @override
  Widget build(BuildContext context) {
    final dotColors = [_brown, _metro, _green];
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        children: [
          CircleAvatar(
            radius: 15,
            backgroundColor: dotColors[index % dotColors.length],
            child: Text('${index + 1}',
                style: const TextStyle(
                    color: Colors.white, fontWeight: FontWeight.w900)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(stop.name,
                    style: const TextStyle(
                        fontWeight: FontWeight.w900, fontSize: 15)),
                Text('${stop.icon} ${stop.category} · ${stop.duration}',
                    style: const TextStyle(
                        color: _inkSoft,
                        fontSize: 11,
                        fontWeight: FontWeight.w700)),
              ],
            ),
          ),
          Text(stop.time,
              style:
                  const TextStyle(fontSize: 13, fontWeight: FontWeight.w900)),
        ],
      ),
    );
  }
}

class _TransitPill extends StatelessWidget {
  const _TransitPill({required this.label, this.blue = false});

  final String label;
  final bool blue;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
          color: (blue ? _metro : _walk).withValues(alpha: .13),
          borderRadius: BorderRadius.circular(99)),
      child: Text(label,
          style: TextStyle(
              color: blue ? _metro : _walk,
              fontSize: 12,
              fontWeight: FontWeight.w900)),
    );
  }
}
