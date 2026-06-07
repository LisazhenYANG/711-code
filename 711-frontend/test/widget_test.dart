import 'package:flutter_test/flutter_test.dart';

import 'package:manyu_711_frontend/app_module.dart';

void main() {
  testWidgets('Manyu app shows the home planning entry',
      (WidgetTester tester) async {
    await tester.pumpWidget(const ManyuApp());

    expect(find.text('我的计划'), findsOneWidget);
    expect(find.text('开始规划 ✨'), findsOneWidget);
  });
}
