import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { MatchRoute } from "../../routes/match/MatchRoute";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/matches/prototype-mirror-guest" element={<MatchRoute />} />
        <Route path="*" element={<Navigate to="/matches/prototype-mirror-guest" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

