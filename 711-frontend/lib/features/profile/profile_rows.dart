part of '../../app_module.dart';

class _PreferenceRow extends StatelessWidget {
  const _PreferenceRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 9),
      child: Row(
        children: [
          Text(label,
              style: const TextStyle(
                  color: _inkSoft, fontWeight: FontWeight.w800)),
          const Spacer(),
          Text(value,
              style: const TextStyle(color: _ink, fontWeight: FontWeight.w900)),
        ],
      ),
    );
  }
}

class _ToggleRow extends StatelessWidget {
  const _ToggleRow({required this.title, required this.sub});

  final String title;
  final String sub;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Row(
        children: [
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
                        height: 1.35,
                        fontWeight: FontWeight.w700)),
              ],
            ),
          ),
          Container(
            width: 46,
            height: 26,
            padding: const EdgeInsets.all(3),
            decoration: BoxDecoration(
                color: _brown, borderRadius: BorderRadius.circular(99)),
            alignment: Alignment.centerRight,
            child: Container(
                width: 20,
                height: 20,
                decoration: const BoxDecoration(
                    color: Colors.white, shape: BoxShape.circle)),
          ),
        ],
      ),
    );
  }
}
