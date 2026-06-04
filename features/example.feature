Feature: Greet a person by name

  As someone learning this template
  I want a tiny example feature
  So that I can see the shape auto-tdd expects before writing my own

  # This is a placeholder. Replace this file (and add more .feature files)
  # with the behaviors you actually want to build, then run /auto-tdd.

  Scenario: Greeting uses the person's name
    Given a person named "Ada"
    When I greet them
    Then the greeting should be "Hello, Ada!"

  Scenario: Greeting a person with no name falls back to a default
    Given a person with no name
    When I greet them
    Then the greeting should be "Hello, friend!"
