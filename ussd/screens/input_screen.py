from ussd.core import UssdHandlerAbstract, UssdResponse
from ussd.screens.serializers import UssdContentBaseSerializer, \
    UssdTextSerializer, NextUssdScreenSerializer, MenuOptionSerializer
from django.utils.encoding import force_str
import re
from rest_framework import serializers
from ussd.screens.menu_screen import MenuScreen
from ussd.graph import Link, Vertex
import typing


class InputValidatorSerializer(UssdTextSerializer):
    regex = serializers.CharField(max_length=255, required=False)
    expression = serializers.CharField(max_length=255, required=False)

    def validate(self, data):
        return super(InputValidatorSerializer, self).validate(data)


class InputSerializer(UssdContentBaseSerializer, NextUssdScreenSerializer):
    input_identifier = serializers.CharField(max_length=100)
    validators = serializers.ListField(
        child=InputValidatorSerializer(),
        required=False
    )
    options = serializers.ListField(
        child=MenuOptionSerializer(),
        required=False
    )


class InputScreen(MenuScreen):
    """

    This screen prompts the user to enter an input

    Fields required:
        - text: this the text to display to the user.
        - input_identifier: input amount entered by users will be saved
                            with this key. To access this in the input
                            anywhere {{ input_identifier }}
        - next_screen: The next screen to go after the user enters
                        input
        - validators:
            - text: This is the message to display when the validation fails
              regex: regex used to validate ussd input. Its mutually exclusive
              with expression
            - expression: if regex is not enough you can use a jinja expression
             will be called ussd request object
              text: This the message thats going to be displayed if expression
              returns False
        - options (This field is optional):
            This is a list of options to display to the user
            each option is a key value pair of option text to display
            and next_screen to redirect if option is selected.
            Example of option:

            .. code-block:: yaml

                   options:
                    - text: option one
                      next_screen: screen_one
                    - text: option two
                      next_screen: screen_two

    Example:
        .. literalinclude:: .././ussd/tests/sample_screen_definition/valid_input_screen_conf.yml
    """

    screen_type = "input_screen"
    serializer = InputSerializer

    def handle_ussd_input(self, ussd_input):
        # 1. Perform validation
        validation_rules = self.screen_content.get("validators", {})
        for validation_rule in validation_rules:
            if 'regex' in validation_rule:
                regex_expression = validation_rule['regex']
                regex = re.compile(regex_expression)
                is_valid = bool(
                    regex.search(
                        force_str(ussd_input)
                    ))
            else:
                is_valid = self.evaluate_jija_expression(
                    validation_rule['expression'],
                    session=self.ussd_request.session,
                    extra_context={self.screen_content['input_identifier']: ussd_input}
                )

            # show error message if validation failed
            if not is_valid:
                return UssdResponse(
                    self.get_text(
                        validation_rule['text']
                    )
                )

        # 2. Save the user input to the session
        self.ussd_request.session[
            self.screen_content['input_identifier']
        ] = ussd_input

        # 3. Check if input matches any explicit options for routing (like a menu screen)
        resolved_next_screen_conf = None

        # Check for numeric options first (if input is a digit)
        if ussd_input.isdigit():
            ussd_input_int = int(ussd_input)
            # self.menu_options is populated in MenuScreen's __init__
            for index, menu_option_obj in enumerate(self.menu_options, 1):
                if index == ussd_input_int:
                    resolved_next_screen_conf = menu_option_obj.next_screen
                    break
        
        # If not routed by numeric option, check for text-based options (input_value)
        # and only if resolved_next_screen_conf is still None
        if not resolved_next_screen_conf:
            for menu_option_obj in self.menu_options:
                if menu_option_obj.index_value == ussd_input: # index_value can be custom text from 'input_value'
                    resolved_next_screen_conf = menu_option_obj.next_screen
                    break

        # 4. Route based on matched option or fallback to screen's primary next_screen
        if resolved_next_screen_conf:
            # resolved_next_screen_conf will be a list of dicts (from NextUssdScreenSerializer)
            # route_options is designed to handle this list.
            return self.route_options(resolved_next_screen_conf)
        else:
            # If no option matched, fall back to the screen's primary next_screen logic
            return self.route_options(self.screen_content.get("next_screen"))

    def get_next_screens(self) -> typing.List[Link]:
        # generate validators links
        links = []
        screen_vertex = Vertex(self.handler)
        for index, validation_screen in enumerate(self.screen_content.get("validators", [])):
            validator_screen_name = self.handler + "_validator_" + str(index + 1)
            validation_vertex = Vertex(validator_screen_name,
                                       self.get_text(validation_screen['text']))
            if 'regex' in validation_screen:
                validation_command = 'regex: ' + validation_screen['regex']
            else:
                validation_command = 'expression: ' + validation_screen['expression']
            links.append(
                Link(screen_vertex,
                     validation_vertex,
                     "validation",
                     "arrow",
                     "dotted"
                     )
            )

            links.append(
                Link(
                    validation_vertex,
                    screen_vertex,
                    validation_command,
                    "arrow",
                    "dotted"
                )
            )

        if isinstance(self.screen_content.get("next_screen"), list):
            for i in self.screen_content.get("next_screen", []):
                links.append(
                    Link(screen_vertex,
                         Vertex(i['next_screen'], ""),
                         i['condition'])
            )
        elif self.screen_content.get('next_screen'):
            links.append(
                Link(
                    screen_vertex,
                    Vertex(self.screen_content['next_screen']),
                    self.screen_content['input_identifier']
                )
            )

        if self.screen_content.get('default_next_screen'):
            links.append(
                Link(
                    screen_vertex,
                    Vertex(self.screen_content['default_next_screen'], ""),
                    self.screen_content['input_identifier']
                )
            )
        return links + super(InputScreen, self).get_next_screens()
