part of '../../app_module.dart';

class _StopCard extends StatelessWidget {
  const _StopCard({
    required this.index,
    required this.stop,
    required this.locked,
    required this.onTap,
    required this.onLock,
    required this.onDelete,
    required this.onTransit,
  });

  final int index;
  final _Stop stop;
  final bool locked;
  final VoidCallback onTap;
  final VoidCallback onLock;
  final VoidCallback onDelete;
  final VoidCallback onTransit;

  @override
  Widget build(BuildContext context) {
    final dotColors = [_brown, _metro, _green];
    return GestureDetector(
      onTap: onTap,
      child: _ClayCard(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 16,
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
                  Text('${stop.time} · ${stop.duration}',
                      style: const TextStyle(
                          color: _inkSoft,
                          fontSize: 12,
                          fontWeight: FontWeight.w800)),
                  const SizedBox(height: 3),
                  Text('${stop.icon} ${stop.name}',
                      style: const TextStyle(
                          fontSize: 17, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 5),
                  Text(stop.note,
                      style: const TextStyle(
                          color: _inkMid,
                          fontSize: 12,
                          height: 1.35,
                          fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 6,
                    children: [
                      _TinyTag(stop.category),
                      GestureDetector(
                          onTap: onTransit, child: _TinyTag(stop.transit)),
                      GestureDetector(
                          onTap: onDelete, child: const _TinyTag('左滑删除')),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            GestureDetector(
              onTap: onLock,
              child: Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: locked ? _brown : _card2,
                ),
                alignment: Alignment.center,
                child: Text(locked ? '🔒' : '🔓',
                    style: const TextStyle(fontSize: 15)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
