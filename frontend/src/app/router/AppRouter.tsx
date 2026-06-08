import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthScreen } from "../../features/auth/AuthScreen";
import { HomeScreen } from "../../features/home/HomeScreen";
import { LobbyScreen } from "../../features/lobby/LobbyScreen";
import { MatchRoute } from "../../routes/match/MatchRoute";
import { ProfileSummaryScreen } from "../../features/profile/ProfileSummaryScreen";
import { PrologueScreen } from "../../features/prologue/PrologueScreen";
import { ResultScreen } from "../../features/result/ResultScreen";
import { StoryCasesScreen } from "../../features/story/StoryCasesScreen";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomeScreen />} />
        <Route path="/login" element={<AuthScreen mode="login" />} />
        <Route path="/signup" element={<AuthScreen mode="signup" />} />
        <Route path="/password-reset" element={<AuthScreen mode="password-reset" />} />
        <Route path="/lobby" element={<LobbyScreen />} />
        <Route path="/story-cases" element={<StoryCasesScreen />} />
        <Route path="/prologue" element={<PrologueScreen />} />
        <Route path="/matches/:matchId/result" element={<ResultScreen />} />
        <Route path="/matches/:matchId" element={<MatchRoute />} />
        <Route path="/profile" element={<ProfileSummaryScreen />} />
        <Route path="/profile-summary" element={<ProfileSummaryScreen />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
