part of '../app_module.dart';

class _AppContent extends StatelessWidget {
  const _AppContent({
    required this.state,
    required this.onMood,
    required this.onGo,
    required this.onToggleLock,
    required this.onDeleteStop,
    required this.onShowOverlay,
    required this.onShowStopDetail,
    required this.onShowTransitForStop,
    required this.onShowRecommendationDetail,
    required this.onToggleRouteChat,
    required this.onRouteChatCommand,
    required this.onApplyChatSuggestedRoute,
    required this.onGenerateRoute,
    required this.onSelectRouteOption,
    required this.onConfirmSelectedRoute,
    required this.onLogin,
    required this.onNextGuideStop,
    required this.onToggleBookingSelection,
    required this.onRefreshCurrentLocation,
    required this.onHeartbeatAdjust,
  });

  final _AppState state;
  final ValueChanged<int> onMood;
  final ValueChanged<ScreenStage> onGo;
  final ValueChanged<int> onToggleLock;
  final ValueChanged<int> onDeleteStop;
  final ValueChanged<_AppOverlay> onShowOverlay;
  final ValueChanged<int> onShowStopDetail;
  final ValueChanged<int> onShowTransitForStop;
  final ValueChanged<int> onShowRecommendationDetail;
  final VoidCallback onToggleRouteChat;
  final Stream<_ChatStreamEvent> Function(String message) onRouteChatCommand;
  final ValueChanged<List<_Stop>> onApplyChatSuggestedRoute;
  final Future<void> Function({String freeText}) onGenerateRoute;
  final ValueChanged<int> onSelectRouteOption;
  final VoidCallback onConfirmSelectedRoute;
  final ValueChanged<String> onLogin;
  final VoidCallback onNextGuideStop;
  final ValueChanged<int> onToggleBookingSelection;
  final Future<void> Function() onRefreshCurrentLocation;
  final Future<void> Function({required String reason}) onHeartbeatAdjust;

  @override
  Widget build(BuildContext context) {
    final screen = switch (state.stage) {
      ScreenStage.home => _HomeScreen(
          activePlan: state.hasActivePlan,
          plan: state.planSummary,
          stops: state.routeStops,
          weather: state.weather,
          onGo: onGo,
          onShowOverlay: onShowOverlay,
        ),
      ScreenStage.mood => _MoodScreen(
          selected: state.selectedMoodIndexes,
          loading: state.routeLoading,
          loadingMessage: state.routeLoadingMessage,
          onMood: onMood,
          onGo: onGo,
          onGenerateRoute: onGenerateRoute,
        ),
      ScreenStage.agent => _AgentScreen(
          stops: state.routeStops,
          routeOptions: state.routeOptions,
          selectedRouteOptionIndex: state.selectedRouteOptionIndex,
          onGo: onGo,
          onSelectRouteOption: onSelectRouteOption,
          onConfirmSelectedRoute: onConfirmSelectedRoute,
          onShowOverlay: onShowOverlay,
        ),
      ScreenStage.route => _RouteScreen(
          stops: state.routeStops,
          lockedStops: state.lockedStopIndexes,
          visibleStopIndexes: state.visibleStopIndexes,
          chatOpen: state.routeChatOpen,
          onGo: onGo,
          onToggleLock: onToggleLock,
          onDeleteStop: onDeleteStop,
          onShowOverlay: onShowOverlay,
          onShowStopDetail: onShowStopDetail,
          onShowTransitForStop: onShowTransitForStop,
          onToggleChat: onToggleRouteChat,
          onChatCommand: onRouteChatCommand,
          onApplySuggestedRoute: onApplyChatSuggestedRoute,
        ),
      ScreenStage.execute => _ExecuteScreen(
          paid: state.bookingPaid,
          bookings: state.bookings,
          selectedBookingIndexes: state.selectedBookingIndexes,
          packingList: state.packingList,
          weather: state.weather,
          onGo: onGo,
          onShowOverlay: onShowOverlay,
          onToggleBookingSelection: onToggleBookingSelection,
        ),
      ScreenStage.ticket => _TicketScreen(bookings: state.bookings, onGo: onGo),
      ScreenStage.history => _HistoryScreen(
          hasArchivedPlan: state.hasArchivedPlan,
          plan: state.planSummary,
          stops: state.routeStops,
          onGo: onGo,
        ),
      ScreenStage.archiveDetail => _ArchiveDetailScreen(
          bookings: state.bookings,
          stops: state.routeStops,
          onGo: onGo,
        ),
      ScreenStage.discover => _DiscoverScreen(
          recommendations: state.recommendations,
          onGo: onGo,
          onShowRecommendationDetail: onShowRecommendationDetail,
        ),
      ScreenStage.prompt => _PromptScreen(onGo: onGo),
      ScreenStage.freeChat => _FreeChatScreen(
          routeLoading: state.routeLoading,
          stops: state.routeStops,
          onGo: onGo,
          onShowOverlay: onShowOverlay,
          onGenerateRoute: onGenerateRoute,
        ),
      ScreenStage.guide => _GuideScreen(
          stops: state.routeStops,
          weather: state.weather,
          stopIndex: state.guideStopIndex,
          visibleStopIndexes: state.visibleStopIndexes,
          currentLat: state.currentLat,
          currentLng: state.currentLng,
          locationLoading: state.locationLoading,
          locationError: state.locationError,
          onGo: onGo,
          onShowOverlay: onShowOverlay,
          onNext: onNextGuideStop,
          onRefreshLocation: onRefreshCurrentLocation,
          onHeartbeatAdjust: onHeartbeatAdjust,
        ),
      ScreenStage.profile => _ProfileScreen(
          loggedIn: state.profileLoggedIn,
          profile: state.profileData,
          onGo: onGo,
          onLogin: onLogin,
        ),
    };
    return SafeArea(
      bottom: false,
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 260),
        child: screen,
      ),
    );
  }
}
