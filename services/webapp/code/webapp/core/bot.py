from .models import Food
from .utils import message_parser

# Setup logging
import logging
logger = logging.getLogger(__name__)

class Bot():

    def answer(self, message):

        parsed = message_parser(message)
        #parsed['food']
        #parsed['amount']
        #parsed['serving'] # s m l
        #parsed['details']
        # Filter foods
        foods = Food.query(parsed['food'])
        if not foods:
            return 'Non ho trovato nessun alimento specifico corrispondente a "{}". Puoi provare ad essere più generale?'.format(parsed['food'])

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
            return 'Non ho trovato nessun alimento specifico corrispondente a "{}". Puoi provare ad essere più generale?'.format(parsed['food'])

        # Compute averages
        if cho_observations:
            cho = round(sum(cho_observations) / len(cho_observations))
        if protein_observations:
            proteins = round(sum(protein_observations) / len(protein_observations))
        if fiber_observations:
            fibers = round(sum(fiber_observations) / len(fiber_observations))
        if fat_observations:
            fat = round(sum(fat_observations) / len(fat_observations))

        # Compose reply
        matching_foods_string = ''
        for food in foods:
            matching_foods_string += '{}, '.format(food.name)
        matching_foods_string = matching_foods_string[0:-2]
        reply =  'Per "{}" ho trovato: "{}". '.format(parsed['food'], matching_foods_string)

        if parsed['details']:
            reply += 'Valori nutrizionali medi: '
            if cho_observations:
                reply += '{}g di carboidrati, '.format(cho)
            if protein_observations:
                reply += '{}g di proteine, '.format(proteins)
            if fiber_observations:
                reply += '{}g di fibre e '.format(fibers)
            if fat_observations:
                reply += '{}g di grassi '.format(fat)
            reply += 'per 100g. '
        else:
            if cho_observations:
                reply += 'Mediamente, {}g di carboidrati per 100g. '.format(cho)

        # Also provide info on typical servings if they are all the same
        # What serving to evaluate
        serving = None
        abort = False
        for food in foods:

            if parsed['serving'] == 's' and food.small_serving is not None:
                if serving is None:
                    serving = food.small_serving
                else:
                    if serving != food.small_serving:
                        abort = True
            elif parsed['serving'] == 'm' and food.medium_serving is not None:
                if serving is None:
                    serving = food.medium_serving
                else:
                    if serving != food.medium_serving:
                        abort = True
            elif parsed['serving'] == 'l' and food.large_serving is not None:
                if serving is not None:
                    serving = food.small_serving
                else:
                    if serving != food.small_serving:
                        abort = True
            else:
                if food.typical_serving is not None:
                    if serving is None:
                        serving = food.typical_serving
                    else:
                        if serving != food.typical_serving:
                            abort = True
            if abort:
                break

        if not abort:
            if parsed['serving'] == 's':
                portion_name = 'piccola'
            elif parsed['serving'] == 'm':
                portion_name = 'media'
            elif parsed['serving'] == 's':
                portion_name = 'grande'
            else:
                portion_name = 'tipica'

            if cho_observations:
                reply += 'Una porzione {} è di circa {}g, per un totale circa {}g di carboidrati'.format(portion_name, serving, round(serving*(cho/100)))
            else:
                reply += 'Una porzione {} è di circa {}g.'.format(portion_name)

        if parsed['amount']:
            pass
        if parsed['serving']:
            pass

        return reply

