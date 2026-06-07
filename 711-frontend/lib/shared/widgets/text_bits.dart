part of '../../app_module.dart';

class _SectionHead extends StatelessWidget {
  const _SectionHead({required this.title, required this.count});

  final String title;
  final String count;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text(title,
            style: const TextStyle(
                fontSize: 18, fontWeight: FontWeight.w900, color: _ink)),
        const Spacer(),
        Text(count,
            style: const TextStyle(
                fontSize: 12, fontWeight: FontWeight.w800, color: _inkSoft)),
      ],
    );
  }
}

class _SoftPill extends StatelessWidget {
  const _SoftPill({required this.label, this.color = Colors.white});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
      decoration: BoxDecoration(
          color: color.withValues(alpha: .86),
          borderRadius: BorderRadius.circular(99)),
      child: Text(label,
          style: const TextStyle(
              color: _inkMid, fontSize: 12, fontWeight: FontWeight.w900)),
    );
  }
}

class _TinyTag extends StatelessWidget {
  const _TinyTag(this.label);

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration:
          BoxDecoration(color: _tag, borderRadius: BorderRadius.circular(99)),
      child: Text(label,
          style: const TextStyle(
              color: _inkMid, fontSize: 11, fontWeight: FontWeight.w800)),
    );
  }
}

class _TopBack extends StatelessWidget {
  const _TopBack({required this.label, required this.onTap});

  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: EdgeInsets.symmetric(
            horizontal: label.isEmpty ? 10 : 12, vertical: 8),
        decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: .8),
            borderRadius: BorderRadius.circular(99)),
        child: Text('←${label.isEmpty ? '' : ' $label'}',
            style:
                const TextStyle(color: _inkMid, fontWeight: FontWeight.w900)),
      ),
    );
  }
}

class _SmallButton extends StatelessWidget {
  const _SmallButton({required this.label, required this.onTap});

  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 8),
        decoration: BoxDecoration(
            color: _brown, borderRadius: BorderRadius.circular(99)),
        child: Text(label,
            style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.w900)),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
      decoration: BoxDecoration(
          color: color.withValues(alpha: .14),
          borderRadius: BorderRadius.circular(99)),
      child: Text(label,
          style: TextStyle(
              color: color, fontSize: 11, fontWeight: FontWeight.w900)),
    );
  }
}

class _TodoLine extends StatelessWidget {
  const _TodoLine({required this.done, required this.label});

  final bool done;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 7),
      child: Row(
        children: [
          CircleAvatar(
              radius: 9,
              backgroundColor: done ? _green : _border,
              child: const Text('✓',
                  style: TextStyle(color: Colors.white, fontSize: 10))),
          const SizedBox(width: 7),
          Text(label,
              style: TextStyle(
                  color: done ? _inkSoft : _inkMid,
                  fontSize: 12,
                  fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}
