part of '../../app_module.dart';

class _PrimaryButton extends StatelessWidget {
  const _PrimaryButton({required this.label, required this.onTap});

  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        height: 56,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: _brown,
          borderRadius: BorderRadius.circular(28),
          boxShadow: [
            BoxShadow(
                color: _brown.withValues(alpha: .28),
                blurRadius: 18,
                offset: const Offset(0, 8)),
          ],
        ),
        child: Text(label,
            style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w900)),
      ),
    );
  }
}
