part of '../../app_module.dart';

class _AgentBubble extends StatelessWidget {
  const _AgentBubble({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const CircleAvatar(
            radius: 18,
            backgroundColor: _brown,
            child: Text('晚',
                style: TextStyle(
                    color: Colors.white, fontWeight: FontWeight.w900))),
        const SizedBox(width: 10),
        Expanded(
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
                color: Colors.white, borderRadius: BorderRadius.circular(20)),
            child: Text(text,
                style: const TextStyle(
                    color: _inkMid, height: 1.45, fontWeight: FontWeight.w700)),
          ),
        ),
      ],
    );
  }
}
