import { useLocation, useParams } from "react-router-dom";
import { RitualDuelScreen } from "../../features/match/RitualDuelScreen";

type MatchRouteState = {
  fromLobbyTransition?: boolean;
  fromPrologueTransition?: boolean;
};

export function MatchRoute() {
  const location = useLocation();
  const { matchId = "prototype-mirror-guest" } = useParams();
  const state = location.state as MatchRouteState | null;

  return (
    <RitualDuelScreen
      matchId={matchId}
      fadeIn={Boolean(state?.fromLobbyTransition || state?.fromPrologueTransition)}
    />
  );
}
