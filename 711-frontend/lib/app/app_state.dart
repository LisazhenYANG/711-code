part of '../app_module.dart';

const Object _unset = Object();

class _AppState {
  const _AppState({
    this.stage = ScreenStage.profile,
    this.previousStage = ScreenStage.profile,
    this.overlay = _AppOverlay.none,
    this.selectedMoodIndexes = const {0},
    this.lockedStopIndexes = const {0},
    this.hiddenStopIndexes = const {},
    this.routeStops = _stops,
    this.routeOptions = const [],
    this.selectedRouteOptionIndex = 0,
    this.routeLoading = false,
    this.routeLoadingMessage = '',
    this.planSummary,
    this.bookings = const [],
    this.packingList = const [],
    this.recommendations = const [],
    this.selectedRecommendationIndex = 0,
    this.weather,
    this.profileData,
    this.hasActivePlan = false,
    this.hasArchivedPlan = false,
    this.profileLoggedIn = false,
    this.routeChatOpen = false,
    this.bookingPaid = false,
    this.selectedBookingIndexes = const {},
    this.guideStopIndex = 0,
    this.selectedStopIndex = 0,
    this.currentLat,
    this.currentLng,
    this.locationLoading = false,
    this.locationError,
  });

  final ScreenStage stage;
  final ScreenStage previousStage;
  final _AppOverlay overlay;
  final Set<int> selectedMoodIndexes;
  final Set<int> lockedStopIndexes;
  final Set<int> hiddenStopIndexes;
  final List<_Stop> routeStops;
  final List<_RouteOption> routeOptions;
  final int selectedRouteOptionIndex;
  final bool routeLoading;
  final String routeLoadingMessage;
  final _PlanSummary? planSummary;
  final List<_BookingItem> bookings;
  final List<String> packingList;
  final List<_RecommendationItem> recommendations;
  final int selectedRecommendationIndex;
  final _WeatherSummary? weather;
  final _UserProfileData? profileData;
  final bool hasActivePlan;
  final bool hasArchivedPlan;
  final bool profileLoggedIn;
  final bool routeChatOpen;
  final bool bookingPaid;
  final Set<int> selectedBookingIndexes;
  final int guideStopIndex;
  final int selectedStopIndex;
  final double? currentLat;
  final double? currentLng;
  final bool locationLoading;
  final String? locationError;

  List<int> get visibleStopIndexes {
    return [
      for (var i = 0; i < routeStops.length; i++)
        if (!hiddenStopIndexes.contains(i)) i,
    ];
  }

  int get selectedTabIndex => switch (stage) {
        ScreenStage.mood => 1,
        ScreenStage.discover => 1,
        ScreenStage.prompt => 1,
        ScreenStage.freeChat => 1,
        ScreenStage.profile => 2,
        _ => 0,
      };

  _AppState goTo(ScreenStage next) {
    final gatedNext = !profileLoggedIn && next != ScreenStage.profile
        ? ScreenStage.profile
        : next;
    return copyWith(
      stage: gatedNext,
      previousStage: stage,
      overlay: _AppOverlay.none,
      hasActivePlan: hasActivePlan || gatedNext.startsPlan,
      hasArchivedPlan: hasArchivedPlan || gatedNext == ScreenStage.guide,
    );
  }

  _AppState toggleMood(int index) {
    final next = Set<int>.of(selectedMoodIndexes);
    next.contains(index) ? next.remove(index) : next.add(index);
    if (next.isEmpty) next.add(index);
    return copyWith(selectedMoodIndexes: next);
  }

  _AppState toggleStopLock(int index) {
    final next = Set<int>.of(lockedStopIndexes);
    next.contains(index) ? next.remove(index) : next.add(index);
    return copyWith(lockedStopIndexes: next);
  }

  _AppState deleteStop(int index) {
    if (lockedStopIndexes.contains(index)) {
      return copyWith(overlay: _AppOverlay.lockInfo);
    }
    final next = Set<int>.of(hiddenStopIndexes)..add(index);
    return copyWith(hiddenStopIndexes: next);
  }

  _AppState restoreStops() {
    return copyWith(hiddenStopIndexes: const {});
  }

  _AppState startRouteGeneration() {
    return copyWith(
      routeLoading: true,
      routeLoadingMessage: '正在理解你的偏好...',
      overlay: _AppOverlay.none,
      routeOptions: const [],
      selectedRouteOptionIndex: 0,
    );
  }

  _AppState startLocating() {
    return copyWith(
      locationLoading: true,
      locationError: null,
    );
  }

  _AppState updateCurrentLocation(double lat, double lng) {
    return copyWith(
      currentLat: lat,
      currentLng: lng,
      locationLoading: false,
      locationError: null,
    );
  }

  _AppState failCurrentLocation(String error) {
    return copyWith(
      locationLoading: false,
      locationError: error,
    );
  }

  _AppState finishRouteGeneration(List<_RouteOption> options) {
    final nextOptions = options;
    final nextStops =
        nextOptions.isNotEmpty && nextOptions.first.stops.isNotEmpty
            ? nextOptions.first.stops
            : _stops;
    final nextBookings = _bookingsFromStops(nextStops);
    return copyWith(
      stage: ScreenStage.agent,
      previousStage: stage,
      overlay: _AppOverlay.none,
      routeStops: nextStops,
      routeOptions: nextOptions,
      selectedRouteOptionIndex: 0,
      routeLoading: false,
      routeLoadingMessage: '',
      bookings: nextBookings,
      hiddenStopIndexes: const {},
      lockedStopIndexes: const {0},
      selectedBookingIndexes: {
        for (var i = 0; i < nextBookings.length; i++) i,
      },
      guideStopIndex: 0,
      selectedStopIndex: 0,
      hasActivePlan: true,
    );
  }

  _AppState selectRouteOption(int index) {
    if (index < 0 || index >= routeOptions.length) return this;
    final selected = routeOptions[index];
    final nextStops = selected.stops.isEmpty ? routeStops : selected.stops;
    final nextBookings = _bookingsFromStops(nextStops);
    return copyWith(
      selectedRouteOptionIndex: index,
      routeStops: nextStops,
      bookings: nextBookings,
      selectedBookingIndexes: {
        for (var i = 0; i < nextBookings.length; i++) i,
      },
    );
  }

  _AppState confirmSelectedRouteOption() {
    return copyWith(
      stage: ScreenStage.route,
      previousStage: stage,
      overlay: _AppOverlay.none,
    );
  }

  _AppState replaceRouteInPlace(List<_Stop> stops) {
    if (stops.isEmpty) return this;
    final nextBookings = _bookingsFromStops(stops);
    return copyWith(
      routeStops: stops,
      bookings: nextBookings,
      hiddenStopIndexes: const {},
      lockedStopIndexes: const {0},
      selectedBookingIndexes: {
        for (var i = 0; i < nextBookings.length; i++) i,
      },
      overlay: _AppOverlay.none,
      guideStopIndex: _clampIndex(guideStopIndex, stops.length),
      selectedStopIndex: _clampIndex(selectedStopIndex, stops.length),
    );
  }

  _AppState failRouteGeneration() {
    return copyWith(routeLoading: false, routeLoadingMessage: '');
  }

  _AppState updateRouteLoadingMessage(String message) {
    return copyWith(routeLoading: true, routeLoadingMessage: message);
  }

  _AppState toggleRouteChat() {
    return copyWith(routeChatOpen: !routeChatOpen);
  }

  _AppState showOverlay(_AppOverlay next) {
    return copyWith(overlay: next);
  }

  _AppState showStopDetail(int index) {
    return copyWith(
      selectedStopIndex: index,
      overlay: _AppOverlay.spot,
    );
  }

  _AppState showRecommendationDetail(int index) {
    return copyWith(
      selectedRecommendationIndex: index,
      overlay: _AppOverlay.recDetail,
    );
  }

  _AppState showTransitForStop(int index) {
    return copyWith(
      selectedStopIndex: index,
      overlay: _AppOverlay.transit,
    );
  }

  _AppState closeOverlay() {
    return copyWith(overlay: _AppOverlay.none);
  }

  _AppState completeBooking() {
    return copyWith(bookingPaid: true, overlay: _AppOverlay.none);
  }

  _AppState toggleBookingSelection(int index) {
    final next = Set<int>.of(selectedBookingIndexes);
    next.contains(index) ? next.remove(index) : next.add(index);
    return copyWith(selectedBookingIndexes: next);
  }

  _AppState updateBookings(List<_BookingItem> nextBookings) {
    return copyWith(
      bookings: nextBookings,
      bookingPaid: nextBookings.any((item) => item.done),
      selectedBookingIndexes:
          _normalizedIndexSet(selectedBookingIndexes, nextBookings.length),
      overlay: _AppOverlay.none,
    );
  }

  _AppState applyDashboard(Map<String, dynamic> data) {
    final activePlan = data['active_plan'];
    final bookingsJson = data['bookings'];
    final recsJson = data['recommendations'];
    final packing = _Stop._stringList(data['packing_list']);
    final routeJson =
        activePlan is Map<String, dynamic> ? activePlan['route'] : null;
    final stops = routeJson is List
        ? [
            for (var i = 0; i < routeJson.length; i++)
              if (routeJson[i] is Map<String, dynamic>)
                _Stop.fromBackend(routeJson[i] as Map<String, dynamic>,
                    index: i),
          ]
        : routeStops;
    final safeStops = stops.isEmpty ? routeStops : stops;
    return copyWith(
      planSummary: activePlan is Map<String, dynamic>
          ? _PlanSummary.fromJson(activePlan)
          : planSummary,
      routeStops: safeStops,
      bookings: bookingsJson is List
          ? [
              for (final item in bookingsJson)
                if (item is Map<String, dynamic>) _BookingItem.fromJson(item),
            ]
          : bookings,
      packingList: packing.isEmpty ? packingList : packing,
      recommendations: recsJson is List
          ? [
              for (final item in recsJson)
                if (item is Map<String, dynamic>)
                  _RecommendationItem.fromJson(item),
            ]
          : recommendations,
      lockedStopIndexes:
          _normalizedIndexSet(lockedStopIndexes, safeStops.length),
      hiddenStopIndexes:
          _normalizedIndexSet(hiddenStopIndexes, safeStops.length),
      guideStopIndex: _clampIndex(guideStopIndex, safeStops.length),
      selectedStopIndex: _clampIndex(selectedStopIndex, safeStops.length),
      selectedBookingIndexes: _normalizedIndexSet(selectedBookingIndexes,
          (bookingsJson is List ? bookingsJson.length : bookings.length)),
      weather: _WeatherSummary.fromDashboard(data),
      hasActivePlan: activePlan is Map<String, dynamic> || hasActivePlan,
    );
  }

  _AppState applyRoutePayload(Map<String, dynamic> data) {
    final plan = data['active_plan'];
    final routeJson = data['route'];
    final bookingsJson = data['bookings'];
    final historyJson = data['history'];
    final lastAction = data['last_action'];
    final nextStops = routeJson is List
        ? [
            for (var i = 0; i < routeJson.length; i++)
              if (routeJson[i] is Map<String, dynamic>)
                _Stop.fromBackend(routeJson[i] as Map<String, dynamic>,
                    index: i),
          ]
        : routeStops;
    final safeStops = nextStops.isEmpty ? routeStops : nextStops;
    final nextLocked = _normalizedIndexSet(
        _intSet(data['locked_indexes']) ?? lockedStopIndexes, safeStops.length);
    final nextHidden = _normalizedIndexSet(
        _intSet(data['hidden_indexes']) ?? hiddenStopIndexes, safeStops.length);
    final archivedNow = historyJson is List && historyJson.isNotEmpty;
    final shouldJumpToHistory = lastAction is Map<String, dynamic> &&
        lastAction['type'] == 'archive';
    return copyWith(
      planSummary: plan is Map<String, dynamic>
          ? _PlanSummary.fromJson(plan)
          : planSummary,
      stage: shouldJumpToHistory ? ScreenStage.history : stage,
      routeStops: safeStops,
      lockedStopIndexes: nextLocked,
      hiddenStopIndexes: nextHidden,
      bookings: bookingsJson is List
          ? [
              for (final item in bookingsJson)
                if (item is Map<String, dynamic>) _BookingItem.fromJson(item),
            ]
          : bookings,
      packingList: _Stop._stringList(data['packing_list']).isEmpty
          ? packingList
          : _Stop._stringList(data['packing_list']),
      hasArchivedPlan: archivedNow || hasArchivedPlan,
      weather: _WeatherSummary.fromDashboard(data),
      overlay: _AppOverlay.none,
      guideStopIndex: _clampIndex(guideStopIndex, safeStops.length),
      selectedStopIndex: _clampIndex(selectedStopIndex, safeStops.length),
      selectedBookingIndexes: _normalizedIndexSet(selectedBookingIndexes,
          (bookingsJson is List ? bookingsJson.length : bookings.length)),
      hasActivePlan: true,
    );
  }

  _AppState applyProfile(_UserProfileData profile) {
    return copyWith(profileData: profile);
  }

  _AppState loginProfile(String phone) {
    final suffix =
        phone.length >= 4 ? phone.substring(phone.length - 4) : phone;
    final nextProfile = (profileData ??
            const _UserProfileData(
              name: '用户',
              phone: '',
              preferences: [],
              modes: [],
              footprints: [],
            ))
        .copyWith(
      name: '用户$suffix',
      phone: phone,
    );
    return copyWith(profileLoggedIn: true, profileData: nextProfile);
  }

  _AppState nextGuideStop() {
    final last = visibleStopIndexes.length - 1;
    if (guideStopIndex >= last) {
      return copyWith(hasArchivedPlan: true, stage: ScreenStage.history);
    }
    return copyWith(guideStopIndex: guideStopIndex + 1);
  }

  _AppState goToTab(int index) {
    if (!profileLoggedIn && index != 2) {
      return goTo(ScreenStage.profile);
    }
    return switch (index) {
      0 => goTo(ScreenStage.home),
      1 => showOverlay(_AppOverlay.plus),
      2 => goTo(ScreenStage.profile),
      _ => this,
    };
  }

  _AppState copyWith({
    ScreenStage? stage,
    ScreenStage? previousStage,
    _AppOverlay? overlay,
    Set<int>? selectedMoodIndexes,
    Set<int>? lockedStopIndexes,
    Set<int>? hiddenStopIndexes,
    List<_Stop>? routeStops,
    List<_RouteOption>? routeOptions,
    int? selectedRouteOptionIndex,
    bool? routeLoading,
    String? routeLoadingMessage,
    _PlanSummary? planSummary,
    List<_BookingItem>? bookings,
    List<String>? packingList,
    List<_RecommendationItem>? recommendations,
    int? selectedRecommendationIndex,
    _WeatherSummary? weather,
    _UserProfileData? profileData,
    bool? hasActivePlan,
    bool? hasArchivedPlan,
    bool? profileLoggedIn,
    bool? routeChatOpen,
    bool? bookingPaid,
    Set<int>? selectedBookingIndexes,
    int? guideStopIndex,
    int? selectedStopIndex,
    double? currentLat,
    double? currentLng,
    bool? locationLoading,
    Object? locationError = _unset,
  }) {
    return _AppState(
      stage: stage ?? this.stage,
      previousStage: previousStage ?? this.previousStage,
      overlay: overlay ?? this.overlay,
      selectedMoodIndexes: selectedMoodIndexes ?? this.selectedMoodIndexes,
      lockedStopIndexes: lockedStopIndexes ?? this.lockedStopIndexes,
      hiddenStopIndexes: hiddenStopIndexes ?? this.hiddenStopIndexes,
      routeStops: routeStops ?? this.routeStops,
      routeOptions: routeOptions ?? this.routeOptions,
      selectedRouteOptionIndex:
          selectedRouteOptionIndex ?? this.selectedRouteOptionIndex,
      routeLoading: routeLoading ?? this.routeLoading,
      routeLoadingMessage: routeLoadingMessage ?? this.routeLoadingMessage,
      planSummary: planSummary ?? this.planSummary,
      bookings: bookings ?? this.bookings,
      packingList: packingList ?? this.packingList,
      recommendations: recommendations ?? this.recommendations,
      selectedRecommendationIndex:
          selectedRecommendationIndex ?? this.selectedRecommendationIndex,
      weather: weather ?? this.weather,
      profileData: profileData ?? this.profileData,
      hasActivePlan: hasActivePlan ?? this.hasActivePlan,
      hasArchivedPlan: hasArchivedPlan ?? this.hasArchivedPlan,
      profileLoggedIn: profileLoggedIn ?? this.profileLoggedIn,
      routeChatOpen: routeChatOpen ?? this.routeChatOpen,
      bookingPaid: bookingPaid ?? this.bookingPaid,
      selectedBookingIndexes:
          selectedBookingIndexes ?? this.selectedBookingIndexes,
      guideStopIndex: guideStopIndex ?? this.guideStopIndex,
      selectedStopIndex: selectedStopIndex ?? this.selectedStopIndex,
      currentLat: currentLat ?? this.currentLat,
      currentLng: currentLng ?? this.currentLng,
      locationLoading: locationLoading ?? this.locationLoading,
      locationError: identical(locationError, _unset)
          ? this.locationError
          : locationError as String?,
    );
  }

  List<_BookingItem> _bookingsFromStops(List<_Stop> stops) {
    return [
      for (final stop in stops)
        if (stop.price.isNotEmpty ||
            stop.category.contains('展') ||
            stop.category.contains('手'))
          _BookingItem(
            icon: stop.icon,
            name: stop.name,
            category: stop.category,
            bookingType: stop.category.contains('展') ? '门票' : '预约',
            time: stop.time,
            statusText: stop.category.contains('展') ? '待支付' : '待预约',
            productName: stop.category.contains('展') ? '普通票' : '体验预约',
            price: stop.price.replaceFirst('普通票 ', ''),
          ),
    ];
  }

  Set<int>? _intSet(Object? value) {
    if (value is! List) return null;
    return {
      for (final item in value)
        if (item is int) item,
    };
  }

  int _clampIndex(int index, int length) {
    if (length <= 0) return 0;
    if (index < 0) return 0;
    if (index >= length) return length - 1;
    return index;
  }

  Set<int> _normalizedIndexSet(Set<int> source, int length) {
    if (length <= 0) return const {};
    return {
      for (final index in source)
        if (index >= 0 && index < length) index,
    };
  }
}

extension _ScreenStageFlow on ScreenStage {
  bool get startsPlan =>
      this == ScreenStage.route ||
      this == ScreenStage.execute ||
      this == ScreenStage.guide;
}

enum _AppOverlay {
  none,
  plus,
  venue,
  venueDetail,
  addPlace,
  meal,
  transit,
  spot,
  recDetail,
  lockInfo,
  payment,
  location,
  heart,
}
