# market score calculator

from apps import app
from apps.database.models import ScanResult, Averages, User, Website, Severity

MARKET_USER_EMAIL = 'marketscan@horangi.com'

def count_scan_severity(scans, severity):
    count = 0
    for scan in scans:
        print("scan = ", scan)
        if scan == None:
            continue
        if scan.severity == severity:
            count += 1
    return count

def store_scores(scores):
    print "storing scores"
    Averages.create(critical=scores[Severity.critical],
                    high=scores[Severity.high],
                    medium=scores[Severity.medium],
                    low=scores[Severity.low],
                    info=scores[Severity.informational])

def calculate_market_scores():
    user = User.query.filter(User.email == MARKET_USER_EMAIL).one()     # get marketscan user
    market_websites = Website.query.filter(Website.user_id == user.id).all()
    scans = ScanResult.query.filter(ScanResult.user_id == user.id).all()
    rank_dict = {}
    for sev in Severity:
        rank_dict[sev] = count_scan_severity(scans, sev) / float(len(market_websites))
    return rank_dict

def main():
    market_scores = calculate_market_scores()
    store_scores(market_scores)


if __name__ == '__main__':
    with app.app_context():
        main()
