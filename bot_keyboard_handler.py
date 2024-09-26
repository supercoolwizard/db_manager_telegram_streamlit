from telebot import types


class KeyboardMaster:
    def __init__(self, bot, command, initial_buttons):
        """
        Initialize the KeyboardMaster class.

        :param bot: The bot instance.
        :param command: The command on which the initial keyboard will appear.
        :param initial_buttons: A list of tuples where each tuple contains (button_text, button_action, next_buttons,
                                requires_input, expected_input).
        """
        self.bot = bot
        self.command = command
        self.initial_buttons = initial_buttons
        self.navigation_stack = []
        self.current_buttons = initial_buttons
        self.waiting_for_input = False  # Flag to indicate if we are waiting for user input
        self.expected_input = None  # Expected input after a button click
        self.next_buttons_after_input = None  # Buttons to display if the input is correct
        self.pending_action_after_input = None  # Action to execute after correct input
        self.setup_command_handler()

    def setup_command_handler(self):
        """Set up the command handler for the bot."""
        @self.bot.message_handler(commands=[self.command])
        def command_handler(message):
            self.navigation_stack = []  # Reset navigation stack on start
            self.display_keyboard(message.chat.id, self.initial_buttons)

    def display_keyboard(self, chat_id, buttons):
        """Display a keyboard with the given buttons."""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=len(buttons))
        for button_text, _, _, _, _ in buttons:
            markup.add(types.KeyboardButton(button_text))
        if self.navigation_stack:
            markup.add(types.KeyboardButton("$$back"))
        self.bot.send_message(chat_id, "Choose an option:", reply_markup=markup)
        self.current_buttons = buttons

    def handle_input(self, message):
        """Handle user input and check if it matches the expected input."""
        if message.text == '$$back':
            self.waiting_for_input = False  # Reset input waiting state

        elif message.text == self.expected_input:
            # If the input is correct, proceed to the next buttons
            # self.bot.send_message(message.chat.id, "Input correct!")
            if self.pending_action_after_input:
                self.pending_action_after_input(message)  # Execute the action (e.g., admin_handler)
            self.navigation_stack.append(self.current_buttons)  # Save current buttons to stack
            self.display_keyboard(message.chat.id, self.next_buttons_after_input)
            self.waiting_for_input = False  # Reset input waiting state
        else:
            # If the input is incorrect, prompt again
            self.bot.send_message(message.chat.id, "Incorrect password, please try again. (or $$back to go back)")

    def setup_button_handler(self):
        """Set up the button handler for dynamic buttons."""
        @self.bot.message_handler(func=lambda message: True)
        def button_handler(message):
            if self.waiting_for_input:
                # If we are waiting for input, handle it
                self.handle_input(message)
                return

            if message.text == "$$back" and self.navigation_stack:
                # Navigate back to the previous level
                self.current_buttons = self.navigation_stack.pop()
                self.display_keyboard(message.chat.id, self.current_buttons)
            else:
                for button_text, button_action, next_buttons, requires_input, expected_input in self.current_buttons:
                    if message.text == button_text:
                        if requires_input:
                            # If input is required, ask for input and store the expected value and action
                            self.bot.send_message(message.chat.id, "Please, enter your password:")
                            self.waiting_for_input = True
                            self.expected_input = expected_input
                            self.next_buttons_after_input = next_buttons
                            self.pending_action_after_input = button_action  # Save the action to execute after correct input
                        else:
                            if button_action:
                                button_action(message)  # Execute the action (e.g., user_handler)
                            if next_buttons:
                                # Push the current buttons to the stack before navigating deeper
                                self.navigation_stack.append(self.current_buttons)
                                self.display_keyboard(message.chat.id, next_buttons)
                        return  # Exit after handling the correct button

