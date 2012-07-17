NEXT = "list_OK"

def parse(mpd_response, client):
    if mpd_response:
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
                    parts = line.split(":")
                    head, tail = parts[0].strip(), ":".join(parts[1:]).strip()
                    if client._last_command == "playlist":
                        response_data[int(head)] = ":".join(tail.split(":")[1:]).strip()
                    elif client._last_command in ("addid", "update"):
                        return int(tail)
                    elif client._last_command == "idle":
#                        client._pending = False
                        return tail
                    else:
                        response_data[head] = tail
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
    else:
        return mpd_response
