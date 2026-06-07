part of '../../app_module.dart';

class _BookingRow extends StatelessWidget {
  const _BookingRow(
      {required this.icon,
      required this.title,
      required this.sub,
      required this.status,
      this.done = false,
      this.selectable = false,
      this.selected = true,
      this.onToggle});

  final String icon;
  final String title;
  final String sub;
  final String status;
  final bool done;
  final bool selectable;
  final bool selected;
  final VoidCallback? onToggle;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration:
          BoxDecoration(color: _card2, borderRadius: BorderRadius.circular(18)),
      child: Row(
        children: [
          if (selectable)
            GestureDetector(
              onTap: onToggle,
              child: Container(
                width: 22,
                height: 22,
                margin: const EdgeInsets.only(right: 10),
                decoration: BoxDecoration(
                  color: selected ? _brown : Colors.white,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: selected ? _brown : _border),
                ),
                alignment: Alignment.center,
                child: Text(
                  selected ? '✓' : '',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
            ),
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
          _StatusBadge(label: status, color: done ? _green : _tan),
        ],
      ),
    );
  }
}
