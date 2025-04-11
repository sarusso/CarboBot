from .models import Food
from .utils import message_parser
from . import emoji

# Setup logging
import logging
logger = logging.getLogger(__name__)

class Bot():

    def answer(self, message):

        parsed = message_parser(message)

        # Set variant
        if parsed['pieces'] :
            variant = 'pieces'
        elif parsed['serving']:
            variant = 'servings'
        else:
            variant = None

        # Query foods on the correct DB (based on variant)
        foods = Food.query(parsed['food'], variant=variant)

        if variant == 'pieces' and not foods:
            # Try removing the "un", "una", etc and re-parse
            if message.startswith('un '):
                message_variant = message[3:]
            elif message.startswith('uno '):
                message_variant = message[4:]
            elif message.startswith('una '):
                message_variant = message[4:]
            else:
                message_variant = message

            if message_variant != message:
                message_variant = message_variant.strip()
                parsed = message_parser(message_variant)
                foods = Food.query(parsed['food'], variant='servings')

        if not foods:
            return 'Non ho trovato nessun alimento per "{}". Puoi provare ad essere più generale?'.format(message)

        # Shortucts
        parsed_food = parsed['food']
        parsed_amount = parsed['amount']
        parsed_pieces = parsed['pieces']     # None, 1, 2,..., 10
        parsed_size = parsed['size']         # s, m, l
        parsed_details = parsed['details']
        parsed_serving = parsed['serving']   # None or 1

        # Process all observations for matching foods
        cho_observations = []
        protein_observations = []
        fiber_observations = []
        fat_observations = []
        for food in foods:
            for observation in food.observations.all():
                if observation.cho is not None:
                    cho_observations.append(observation.cho)
                if observation.proteins is not None:
                    protein_observations.append(observation.proteins)
                if observation.fibers is not None:
                    fiber_observations.append(observation.fibers)
                if observation.fat is not None:
                    fat_observations.append(observation.fat)

        if not cho_observations and not protein_observations and not fiber_observations and not fat_observations:
            return 'Non ho trovato nessun alimento per "{}". Puoi provare ad essere più generale?'.format(message)

        # Compute averages
        if cho_observations:
            cho = round(sum(cho_observations) / len(cho_observations))
            cho_variation = 1 - (min(cho_observations)/max(cho_observations))
        if protein_observations:
            proteins = round(sum(protein_observations) / len(protein_observations))
        if fiber_observations:
            fibers = round(sum(fiber_observations) / len(fiber_observations))
        if fat_observations:
            fat = round(sum(fat_observations) / len(fat_observations))

        # Compose reply
        if len(foods) == 1:
            reply =  'Ho trovato "{}". '.format(foods[0].name)
        else:
            matching_foods_string = ''
            for food in foods:
                matching_foods_string += '\n• {}; '.format(food.name)
            matching_foods_string = matching_foods_string[0:-2]
            reply =  'Per "{}" ho trovato: {}.\n'.format(message, matching_foods_string)

        # Set unit
        units = []
        for food in foods:
            if food.liquid:
                if 'ml' not in units:
                    units.append('ml')
            else:
                if 'g' not in units:
                    units.append('g')
        unit = '/'.join(units)

        if cho_variation > 0.15:
            reply += '️{} Varibilità fra i risultati! (~{}%).\n'.format(emoji.warning, int(cho_variation*100))

        if parsed_details:
            reply += 'Valori nutrizionali medi: '
            if cho_observations:
                reply += '{}g di carboidrati, '.format(cho)
            if protein_observations:
                reply += '{}g di proteine, '.format(proteins)
            if fiber_observations:
                reply += '{}g di fibre e '.format(fibers)
            if fat_observations:
                reply += '{}g di grassi '.format(fat)
            reply += 'per 100{}. '.format(unit)
        else:
            if cho_observations:
                reply += 'Mediamente, *{}g/* di carboidrati per *100{}/*. '.format(cho, unit)


        # Force serving if nothing specified
        if not parsed_amount and not parsed_pieces and not parsed_serving:
            parsed_serving = 1


        #-------------------------------
        # Were we given an amount?
        #-------------------------------
        if parsed_amount:
            # Compute the value for the given amount
            if cho_observations:
                reply += 'Per *{}{}/*, il totale di carboidrati è di circa *{}g/*.'.format(parsed['amount'],
                                                                                           unit,
                                                                                           round(parsed['amount']*(cho/100)))

        #-------------------------------
        # Were we given a serving ?
        #-------------------------------
        elif parsed_serving:

            if not parsed_size:
                serving_size =  'm'
            else:
                serving_size = parsed_size

            servings = []
            servings_all_the_same = True

            for food in foods:

                # Small serving
                if serving_size == 's' and food.small_serving is not None:
                    if not servings:
                        servings.append(food.small_serving)
                    else:
                        if servings[-1] != food.small_serving:
                            servings_all_the_same = False
                        servings.append(food.small_serving)

                # Medium serving
                if serving_size == 'm' and food.medium_serving is not None:
                    if not servings:
                        servings.append(food.medium_serving)
                    else:
                        if servings[-1] != food.medium_serving:
                            servings_all_the_same = False
                        servings.append(food.medium_serving)

                # Large serving
                if serving_size == 'l' and food.large_serving is not None:
                    if not servings:
                        servings.append(food.large_serving)
                    else:
                        if servings[-1] != food.large_serving:
                            servings_all_the_same = False
                        servings.append(food.large_serving)

            if servings:
                if not servings_all_the_same:
                    # Compute average
                    serving_amount = round(sum(servings)/len(servings))
                else:
                    serving_amount = servings[0]
            else:
                serving_amount = None

            if serving_amount:
                if serving_size == 's':
                    size_name = 'piccola'
                elif serving_size == 'm':
                    size_name = 'media'
                elif serving_size == 'l':
                    size_name = 'grande'

                if cho_observations:
                    if servings_all_the_same:
                        reply += 'Una porzione {} è di circa *{}{}/*, per un totale di circa *{}g/* di carboidrati.'.format(size_name,
                                                                                                                            serving_amount,
                                                                                                                            unit,
                                                                                                                            round(serving_amount*(cho/100)))
                    else:
                        reply += 'In media, una porzione {} è di circa *{}{}/*, per un totale di circa *{}g/* di carboidrati.'.format(size_name,
                                                                                                                                      serving_amount,
                                                                                                                                      unit,
                                                                                                                                      round(serving_amount*(cho/100)))


        #-------------------------------
        # Were we given a piece number?
        #-------------------------------
        elif parsed_pieces:

            if not parsed_size:
                piece_size =  'm'
            else:
                piece_size = parsed_size

            pieces = []
            pieces_all_the_same = True

            for food in foods:

                # Small piece
                if piece_size == 's' and food.small_piece is not None:
                    if not pieces:
                        pieces.append(food.small_piece)
                    else:
                        if pieces[-1] != food.small_piece:
                            pieces_all_the_same = False
                        pieces.append(food.small_piece)

                # Medium piece
                if (piece_size == 'm' or not piece_size) and food.medium_piece is not None:
                    if not pieces:
                        pieces.append(food.medium_piece)
                    else:
                        if pieces[-1] != food.medium_piece:
                            pieces_all_the_same = False
                        pieces.append(food.medium_piece)

                # Large piece
                if piece_size == 'l' and food.large_piece is not None:
                    if not pieces:
                        pieces.append(food.large_piece)
                    else:
                        if pieces[-1] != food.large_piece:
                            pieces_all_the_same = False
                        pieces.append(food.large_piece)

            if pieces:
                if not pieces_all_the_same:
                    # Compute average
                    piece_amount = round(sum(pieces)/len(pieces))
                else:
                    piece_amount = pieces[0]
            else:
                piece_amount = None

            postfix = 'o' if parsed_pieces == 1 else 'i'

            if piece_amount:
                if piece_size == 's':
                    size_name = 'piccolo' if parsed_pieces == 1 else 'piccoli '
                elif piece_size == 'm' or not piece_size:
                    size_name = 'medio' if parsed_pieces == 1 else 'medi'
                elif piece_size == 'l':
                    size_name = 'grande' if parsed_pieces == 1 else 'grandi '

                if cho_observations:
                    if pieces_all_the_same:
                        reply += '{} pezz{} {} sono circa *{}{}/*, per un totale di circa *{}g/* di carboidrati.'.format(parsed_pieces,
                                                                                                                         postfix,
                                                                                                                         size_name,
                                                                                                                         piece_amount*parsed_pieces,
                                                                                                                         unit,
                                                                                                                         round(piece_amount*parsed_pieces*(cho/100)))
                    else:
                        reply += 'In media, {} pezz{} {} sono circa *{}{}/*, per un totale di circa *{}g/* di carboidrati.'.format(parsed_pieces,
                                                                                                                                   postfix,
                                                                                                                                   size_name,
                                                                                                                                   piece_amount*parsed_pieces,
                                                                                                                                   unit,
                                                                                                                                   round(piece_amount*parsed_pieces*(cho/100)))


        #-------------------------------
        # Otherwise, just provide stats
        #-------------------------------
        else:
            pass


        return reply

