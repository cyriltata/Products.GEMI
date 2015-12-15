# ============================================================================
# DEXTERITY ROBOT TESTS
# ============================================================================
#
# Run this robot test stand-alone:
#
#  $ bin/test -s Products.GEMI -t test_gemifolder.robot --all
#
# Run this robot test with robot server (which is faster):
#
# 1) Start robot server:
#
# $ bin/robot-server --reload-path src Products.GEMI.testing.PRODUCTS_GEMI_ACCEPTANCE_TESTING
#
# 2) Run robot tests:
#
# $ bin/robot src/plonetraining/testing/tests/robot/test_gemifolder.robot
#
# See the http://docs.plone.org for further details (search for robot
# framework).
#
# ============================================================================

*** Settings *****************************************************************

Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot

Library  Remote  ${PLONE_URL}/RobotRemote

Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***************************************************************

Scenario: As a site administrator I can add a Gemifolder
  Given a logged-in site administrator
    and an add gemifolder form
   When I type 'My Gemifolder' into the title field
    and I submit the form
   Then a gemifolder with the title 'My Gemifolder' has been created

Scenario: As a site administrator I can view a Gemifolder
  Given a logged-in site administrator
    and a gemifolder 'My Gemifolder'
   When I go to the gemifolder view
   Then I can see the gemifolder title 'My Gemifolder'


*** Keywords *****************************************************************

# --- Given ------------------------------------------------------------------

a logged-in site administrator
  Enable autologin as  Site Administrator

an add gemifolder form
  Go To  ${PLONE_URL}/++add++Gemifolder

a gemifolder 'My Gemifolder'
  Create content  type=Gemifolder  id=my-gemifolder  title=My Gemifolder


# --- WHEN -------------------------------------------------------------------

I type '${title}' into the title field
  Input Text  name=form.widgets.title  ${title}

I submit the form
  Click Button  Save

I go to the gemifolder view
  Go To  ${PLONE_URL}/my-gemifolder
  Wait until page contains  Site Map


# --- THEN -------------------------------------------------------------------

a gemifolder with the title '${title}' has been created
  Wait until page contains  Site Map
  Page should contain  ${title}
  Page should contain  Item created

I can see the gemifolder title '${title}'
  Wait until page contains  Site Map
  Page should contain  ${title}
