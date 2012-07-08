NEXT = "list_OK"

def parse(mpd_response, client):
    if NEXT in mpd_response:
    # TODO: extend the parser to handle this
        pass
    else:
        # those are lists
        if client._last_command in ("commands", "notcommands", "list", \
                        "listplaylist", "tagtypes", "urlhandlers"):
            return [":".join(com.split(":")[1:]).strip() for com in mpd_response]

        #  those are dictionaries or single values
        elif client._last_command in ("status", "currentsong", "stats", \
                    "replay_gain_status", "playlist", "addid", "idle", "update"):
            response_data = {}
            for line in mpd_response:
                line_data = [d.strip() for d in line.split(":")]
                if client._last_command == "playlist":
                    response_data[int(line_data[0])] = line_data[2]
                elif client._last_command in ("addid", "update"):
                    return int(line_data[1])
                elif client._last_command == "idle":
                    client._pending = False
                    return line_data[1]
                else:
                    response_data[line_data[0]] = line_data[1]
            return response_data

                # those are lists of dictionaries
        elif client._last_command in ("playlistid", "playlistfind", \
                    "playlistsearch", "playlistinfo", "plchanges", "plchangesposid", \
                    "listplaylistinfo",	"search", "find", "listplaylists", "outputs"):
            items = []
            seen_attrs = []
            tmp_dict = {}
            for line in mpd_response:
                line_data = [d.strip() for d in line.split(":")]
                _attr, value = line_data[0], line_data[1]
                # TODO: check if there are duplicates
                if _attr in seen_attrs:
                    items.append(tmp_dict)
                    tmp_dict = {}
                    seen_attrs = []
                    seen_attrs.append(_attr)
                    tmp_dict[_attr] = value
                elif line == mpd_response[-1]:
                    tmp_dict[_attr] = value
                    items.append(tmp_dict)
                    tmp_dict = {}
                    seen_attrs = []
                    seen_attrs.append(_attr)
                else:
                    seen_attrs.append(_attr)
                    tmp_dict[_attr] = value
            return items

