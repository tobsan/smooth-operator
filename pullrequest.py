import requests

class PullRequest:
    seen_prs_file = "seen_prs"

    repos = [
            {
                "channel": "#pelux",
                "name": "meta-bistro",
                "uri": "https://api.github.com/repos/pelagicore/meta-bistro/pulls"
            },
            {
                "channel": "#pelux",
                "name": "meta-pelux",
                "uri": "https://api.github.com/repos/pelagicore/meta-pelux/pulls"
            },
            {
                "channel": "#pelux",
                "name": "meta-template",
                "uri": "https://api.github.com/repos/pelagicore/meta-template/pulls"
            },
            {
                "channel": "#pelux",
                "name": "pelux-manifests",
                "uri": "https://api.github.com/repos/pelagicore/pelux-manifests/pulls"
            },
            {
                "channel": "#pelux",
                "name": "pelux-sde",
                "uri": "https://api.github.com/repos/pelagicore/pelux-sde/pulls"
            },
            {
                "channel": "#pelux",
                "name": "software-factory",
                "uri": "https://api.github.com/repos/pelagicore/software-factory/pulls"
            },
            {
                "channel": "#pelux",
                "name": "software-factory-blueprint",
                "uri": "https://api.github.com/repos/pelagicore/software-factory-blueprint/pulls"
            },
            {
                "channel": "#pelux",
                "name": "pelux.io",
                "uri": "https://api.github.com/repos/pelagicore/pelux.io/pulls"
            },
            {
                "channel": "#pelux",
                "name": "smooth-operator",
                "uri": "https://api.github.com/repos/jonte/smooth-operator/pulls"
            }
            ]

    def has_seen_before(self, obj):
        try:
            with open(self.seen_prs_file, "r") as f:
                for line in f.readlines():
                    if line.strip() == str(obj["id"]):
                        return True
        except IOError:
            pass

        return False

    def mark_pr_as_seen(self, obj):
        with open(self.seen_prs_file, "a") as f:
            f.write(str(obj["id"]) + "\n")


    def prettyprint(self, repo_name, obj):
        return "New PR in " + repo_name             \
                            + ": '" + obj["title"]  \
                            + "' by "               \
                            + obj["user"]["login"]  \
                            + " - "                 \
                            + obj["html_url"]

    def check_all(self):
        for repo in self.repos:
            r = requests.get(repo["uri"])
            if r.status_code != 200:
                print("Error fetching %s", repo["name"])
                break

            prs = r.json()
            for pr in prs:
                if not self.has_seen_before(pr):
                    self.mark_pr_as_seen(pr)
                    yield {"channel": repo["channel"],
                            "message": self.prettyprint(repo["name"], pr)}

# Test
if __name__ == "__main__":
    p = PullRequest()
    for line in p.check_all():
        print(line["message"])
