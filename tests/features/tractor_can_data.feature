Feature: Tractor CAN Data Reception
  As the AFS FastAPI system
  I want to receive and interpret standard tractor data from the ISOBUS network
  So that I can monitor tractor status and integrate with farm management systems

  Scenario Outline: Receiving <Data Type> Data
    Given the AFS FastAPI system is connected to an ISOBUS network
    And a Tractor ECU is present on the network
    When the Tractor ECU broadcasts <Data Type> (PGN <PGN>, SPN <SPN>) with value <Value>
    Then the AFS FastAPI system should receive and correctly parse the <Data Type> value as <Value>

    Examples:
      | Data Type         | PGN    | SPN | Value |
      | Engine Speed      | 61444  | 190 | 2000  |
      | Vehicle Speed     | 65265  | 84  | 50    |
      | Fuel Level        | 65276  | 96  | 75    |
      | GPS Coordinates   | 65267  | 584 | 12345 |

  Scenario: Handling Corrupted CAN Messages
    Given the AFS FastAPI system is connected to an ISOBUS network
    And a Tractor ECU is present on the network
    When a corrupted CAN message is broadcast on the network
    Then the AFS FastAPI system should log the error and discard the message

  Scenario: Handling Unknown PGNs
    Given the AFS FastAPI system is connected to an ISOBUS network
    And a Tractor ECU is present on the network
    When an unknown PGN is broadcast on the network
    Then the AFS FastAPI system should log the unknown PGN and ignore the message

  Scenario: Receiving Multi-frame Messages
    Given the AFS FastAPI system is connected to an ISOBUS network
    And a Tractor ECU is present on the network
    When the Tractor ECU broadcasts a multi-frame message
    Then the AFS FastAPI system should receive and reassemble the complete message

  Scenario: Filtering Specific PGNs
    Given the AFS FastAPI system is configured to filter for specific PGNs
    And the AFS FastAPI system is connected to an ISOBUS network
    And a Tractor ECU is present on the network
    When multiple PGNs are broadcast on the network
    Then the AFS FastAPI system should only process the configured PGNs
