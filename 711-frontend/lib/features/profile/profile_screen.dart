part of '../../app_module.dart';

class _ProfileScreen extends StatefulWidget {
  const _ProfileScreen({
    required this.loggedIn,
    required this.profile,
    required this.onGo,
    required this.onLogin,
  });

  final bool loggedIn;
  final _UserProfileData? profile;
  final ValueChanged<ScreenStage> onGo;
  final ValueChanged<String> onLogin;

  @override
  State<_ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<_ProfileScreen> {
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _codeController = TextEditingController();
  String _sentCode = '';
  String? _error;

  @override
  void dispose() {
    _phoneController.dispose();
    _codeController.dispose();
    super.dispose();
  }

  void _sendCode() {
    final phone = _phoneController.text.trim();
    if (!_isValidPhone(phone)) {
      setState(() => _error = '请输入 11 位手机号');
      return;
    }
    final generated = (100000 + math.Random().nextInt(900000)).toString();
    setState(() {
      _sentCode = generated;
      _error = null;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('验证码已发送：$generated（demo）'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _verifyAndLogin() {
    final phone = _phoneController.text.trim();
    final code = _codeController.text.trim();
    if (!_isValidPhone(phone)) {
      setState(() => _error = '请输入 11 位手机号');
      return;
    }
    if (_sentCode.isEmpty) {
      setState(() => _error = '请先发送验证码');
      return;
    }
    if (code != _sentCode) {
      setState(() => _error = '验证码不正确');
      return;
    }
    setState(() => _error = null);
    widget.onLogin(phone);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('登录成功'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  bool _isValidPhone(String phone) => RegExp(r'^1\d{10}$').hasMatch(phone);

  @override
  Widget build(BuildContext context) {
    final profile = widget.profile;
    if (!widget.loggedIn) {
      return Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(24, 36, 24, 36),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 300),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 74,
                  height: 74,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: const LinearGradient(
                      colors: [Color(0xFFFFD5C7), Color(0xFFF6EFFF)],
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFFB85E36).withValues(alpha: .14),
                        blurRadius: 22,
                        offset: const Offset(0, 10),
                      ),
                    ],
                  ),
                  alignment: Alignment.center,
                  child: const Text('📱', style: TextStyle(fontSize: 32)),
                ),
                const SizedBox(height: 18),
                const Text(
                  '登录后开始今日漫游',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900),
                ),
                const SizedBox(height: 18),
                _ClayCard(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _LoginField(
                        controller: _phoneController,
                        hintText: '请输入手机号',
                        keyboardType: TextInputType.phone,
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          Expanded(
                            child: _LoginField(
                              controller: _codeController,
                              hintText: '验证码',
                              keyboardType: TextInputType.number,
                            ),
                          ),
                          const SizedBox(width: 8),
                          GestureDetector(
                            onTap: _sendCode,
                            child: Container(
                              height: 46,
                              padding:
                                  const EdgeInsets.symmetric(horizontal: 14),
                              alignment: Alignment.center,
                              decoration: BoxDecoration(
                                color: const Color(0xFFF6E2DA),
                                borderRadius: BorderRadius.circular(16),
                              ),
                              child: const Text(
                                '发送验证码',
                                style: TextStyle(
                                  color: _brown,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w900,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                      if (_error != null) ...[
                        const SizedBox(height: 10),
                        Text(
                          _error!,
                          style: const TextStyle(
                            color: Color(0xFFB0482E),
                            fontSize: 12,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ],
                      const SizedBox(height: 14),
                      _PrimaryButton(label: '登录 / 注册', onTap: _verifyAndLogin),
                      const SizedBox(height: 10),
                      const Text(
                        '当前为 demo 验证码流程，发送后会直接显示验证码。',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: _inkSoft,
                          fontSize: 11,
                          height: 1.4,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return _ScreenScroll(
      key: const ValueKey('profile'),
      child: Column(
        children: [
          const SizedBox(height: 8),
          Container(
            width: 92,
            height: 92,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                  colors: [Color(0xFFFFD5C7), Color(0xFFF0ECFF)]),
            ),
            alignment: Alignment.center,
            child: const Text('👤', style: TextStyle(fontSize: 44)),
          ),
          const SizedBox(height: 10),
          Text(widget.loggedIn ? (profile?.name ?? '用户') : '手机验证码登录',
              style:
                  const TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          _SmallButton(label: '已登录', onTap: () {}),
          const SizedBox(height: 18),
          if (widget.loggedIn)
            _ClayCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('关于你',
                      style:
                          TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 12),
                  if ((profile?.phone ?? '').isNotEmpty)
                    _PreferenceRow(label: '手机号', value: profile!.phone),
                  for (final pref in (profile?.preferences ??
                      const [
                        {'label': '出行风格', 'value': '慢慢逛型'},
                        {'label': '饮食偏好', 'value': '清淡 / 咖啡'},
                        {'label': '交通偏好', 'value': '地铁优先'},
                      ]))
                    _PreferenceRow(
                      label: '${pref['label'] ?? ''}',
                      value: '${pref['value'] ?? ''}',
                    ),
                ],
              ),
            ),
          if (widget.loggedIn)
            const SizedBox(height: 14),
          if (widget.loggedIn)
            _ClayCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('出行模式',
                      style:
                          TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 10),
                  for (final mode in (profile?.modes ??
                      const [
                        {'title': '导览模式', 'sub': '只看下一站和票根，界面干净不乱'},
                        {'title': '心动模式', 'sub': '实时感知天气、排队和定位变化'},
                      ]))
                    _ToggleRow(
                      title: '${mode['title'] ?? ''}',
                      sub: '${mode['sub'] ?? ''}',
                    ),
                ],
              ),
            ),
          if (widget.loggedIn) ...[
            const SizedBox(height: 14),
            _ClayCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('探索足迹',
                      style:
                          TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (final tag in (profile?.footprints ??
                          const ['虹口区', '艺术展', '咖啡', '手作']))
                        _TinyTag(tag),
                    ],
                  ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 100),
        ],
      ),
    );
  }
}

class _LoginField extends StatelessWidget {
  const _LoginField({
    required this.controller,
    required this.hintText,
    required this.keyboardType,
  });

  final TextEditingController controller;
  final String hintText;
  final TextInputType keyboardType;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      style: const TextStyle(
        color: _ink,
        fontSize: 14,
        fontWeight: FontWeight.w800,
      ),
      decoration: InputDecoration(
        hintText: hintText,
        hintStyle: const TextStyle(
          color: _inkSoft,
          fontSize: 13,
          fontWeight: FontWeight.w700,
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: _border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: _border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: _brown, width: 1.4),
        ),
      ),
    );
  }
}
