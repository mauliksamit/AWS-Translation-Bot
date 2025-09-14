import json
import boto3

# Initialize the Amazon Translate client
translate = boto3.client('translate')

def lambda_handler(event, context):

    print(json.dumps(event))

    slots = event['sessionState']['intent']['slots']
    invocation_source = event['invocationSource']

    text_to_translate = slots.get('text', {}).get('value', {}).get('interpretedValue')
    target_language = slots.get('language', {}).get('value', {}).get('interpretedValue')

    if invocation_source == 'DialogCodeHook':
        if not text_to_translate:
            return {
                "sessionState": {
                    "dialogAction": {
                        "type": "ElicitSlot",
                        "slotToElicit": "text"  # Correct slot name
                    },
                    "intent": event['sessionState']['intent']
                }
            }

        if not target_language:
            return {
                "sessionState": {
                    "dialogAction": {
                        "type": "ElicitSlot",
                        "slotToElicit": "language"  # Correct slot name
                    },
                    "intent": event['sessionState']['intent']
                }
            }
        
        return {
            "sessionState": {
                "dialogAction": {
                    "type": "Delegate"
                },
                "intent": event['sessionState']['intent']
            }
        }

    # This block handles the "Fulfillment" code hook.
    # This part of the code is only executed after all slots are filled.
    if invocation_source == 'FulfillmentCodeHook':
        # Convert the full language name to a Boto3-compatible language code
        lang_codes = {
            'Spanish': 'es',
            'French': 'fr',
            'German': 'de',
            'Italian': 'it',
            'Japanese': 'ja'
        }
        
        target_lang_code = lang_codes.get(target_language.lower(), None)

        if not target_lang_code:
            return {
                "sessionState": {
                    "dialogAction": {
                        "type": "Close"
                    },
                    "intent": event['sessionState']['intent'],
                    "messages": [
                        {
                            "contentType": "PlainText",
                            "content": f"Sorry, I can't translate to {target_language}. Please choose from Spanish, French, German, Italian, Japanese, Chinese, or Arabic."
                        }
                    ]
                }
            }

        translated_text = ""
        try:
            # Call the Amazon Translate service
            response = translate.translate_text(
                Text=text_to_translate,
                SourceLanguageCode='auto',
                TargetLanguageCode=target_lang_code
            )
            translated_text = response['TranslatedText']
        except Exception as e:
            print(f"Error calling Amazon Translate: {e}")
            return {
                "sessionState": {
                    "dialogAction": {
                        "type": "Close"
                    },
                    "intent": event['sessionState']['intent'],
                    "messages": [
                        {
                            "contentType": "PlainText",
                            "content": "An error occurred while translating. Please try again."
                        }
                    ]
                }
            }


        final_response = {
            "sessionState": {
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    'name': event['sessionState']['intent']['name'],
                    'slots': event['sessionState']['intent']['slots'],
                    'state': 'Fulfilled'
                },
                "messages": [
                    {
                        "contentType": "PlainText",
                        "content": f"The translated text is: {translated_text}"
                    }
                ]
            }
        }
        
        return final_response