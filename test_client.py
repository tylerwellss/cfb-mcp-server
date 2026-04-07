from cfbd_client import get_team_info, get_game_results

# Quick sanity check
info = get_team_info("Missouri", 2024)
print(info)

games = get_game_results("Missouri", 2024)
for g in games:
    print(g)