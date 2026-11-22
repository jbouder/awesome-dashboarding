"""Roles, an EMEA-only user, and a row-level security rule, for the Part 2 demo.

Runs inside Superset's app context after bootstrap.py has made the datasets.
Safe to run again.

  Lab viewer   read-only access to the lab's three datasets and dashboards
  EMEA only    a row-level security rule: region = 'EMEA'
  emea         a user with both roles. Sign in as emea / emea-viewer-1 and
               every chart shows EMEA only
"""

from superset.app import create_app

app = create_app()

with app.app_context():
    from superset.connectors.sqla.models import RowLevelSecurityFilter, SqlaTable
    from superset.extensions import db
    from superset.extensions import security_manager as sm

    datasets = db.session.query(SqlaTable).filter(SqlaTable.schema == "metrics").all()
    if not datasets:
        raise SystemExit("[superset-security] no datasets yet; run superset-bootstrap first")

    viewer = sm.find_role("Lab viewer") or sm.add_role("Lab viewer")
    gamma = sm.find_role("Gamma")
    for pv in gamma.permissions:
        if pv not in viewer.permissions:
            viewer.permissions.append(pv)
    for ds in datasets:
        pv = sm.add_permission_view_menu("datasource_access", ds.get_perm())
        if pv not in viewer.permissions:
            viewer.permissions.append(pv)
    db_pv = sm.add_permission_view_menu("database_access", datasets[0].database.get_perm())
    if db_pv not in viewer.permissions:
        viewer.permissions.append(db_pv)

    emea_role = sm.find_role("EMEA only") or sm.add_role("EMEA only")

    rule = db.session.query(RowLevelSecurityFilter).filter_by(name="EMEA only").one_or_none()
    if rule is None:
        rule = RowLevelSecurityFilter(
            name="EMEA only",
            filter_type="Regular",
            clause="region = 'EMEA'",
            description="Part 2 demo: this role sees EMEA rows only.",
        )
        db.session.add(rule)
    rule.tables = datasets
    rule.roles = [emea_role]

    if sm.find_user(username="emea") is None:
        sm.add_user(
            "emea", "EMEA", "Viewer", "emea@dashlab.local", [viewer, emea_role], password="emea-viewer-1"
        )
    db.session.commit()
    print(f"[superset-security] Lab viewer role on {len(datasets)} datasets, EMEA only rule, user emea")
