import 'dart:async';
import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'platform/amap_route_view_stub.dart'
    if (dart.library.html) 'platform/amap_route_view_web.dart';
import 'platform/current_location_service_stub.dart'
    if (dart.library.html) 'platform/current_location_service_web.dart';
import 'platform/open_external_url_stub.dart'
    if (dart.library.html) 'platform/open_external_url_web.dart';

part 'shared/theme/app_colors.dart';
part 'app/manyu_app.dart';
part 'app/screen_stage.dart';
part 'app/app_state.dart';
part 'app/shell.dart';
part 'app/app_content.dart';
part 'app/app_overlays.dart';
part 'services/manyou_api.dart';
part 'models/mood_option.dart';
part 'models/backend_models.dart';
part 'models/route_option.dart';
part 'features/home/home_screen.dart';
part 'features/planning/mood_screen.dart';
part 'features/planning/agent_screen.dart';
part 'features/route/route_screen.dart';
part 'features/execute/execute_screen.dart';
part 'features/profile/profile_screen.dart';
part 'features/route/route_preview_card.dart';
part 'features/planning/mood_card.dart';
part 'features/route/stop_card.dart';
part 'features/route/route_map.dart';
part 'shared/widgets/ambient_background.dart';
part 'shared/widgets/clay_card.dart';
part 'shared/widgets/screen_scroll.dart';
part 'shared/widgets/bottom_tabs.dart';
part 'shared/widgets/buttons.dart';
part 'shared/widgets/text_bits.dart';
part 'features/planning/agent_bubble.dart';
part 'features/route/route_line_item.dart';
part 'features/route/map_node.dart';
part 'features/execute/booking_row.dart';
part 'features/profile/profile_rows.dart';
part 'features/extra/extra_screens.dart';
part 'shared/widgets/blob.dart';
part 'shared/widgets/action_sheets.dart';
part 'models/stop.dart';
part 'data/mood_options_data.dart';
part 'data/stops_data.dart';
