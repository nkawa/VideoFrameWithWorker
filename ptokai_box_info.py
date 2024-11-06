

# すべての座標は中心の値を示してます

from enum import Enum

class Slot(Enum):
    INSPECT = 1
    SORT = 2
    PUT_AWAY_2F_3F = 3
    PUT_AWAY_4F_5F = 4

inspect_slots = {'1': (5025, 1465), '2': (5145, 1465), '3': (5275, 1465),
                              '4': (5025, 1650), '5': (5145, 1650), '6': (5275, 1650), 
                              '7': (5025, 1830), '8': (5145, 1830), '9': (5275, 1830),
                              '10': (5025, 2020), '11': (5145, 2020), '12': (5275, 2020),
                              '13': (5025, 2205), '14': (5145, 2205), '15': (5275, 2205), 
                              '16': (5025, 2375), '17': (5145, 2375), '18': (5275, 2375),  
                              '19': (5025, 2490), '20': (5145, 2490), '21': (5275, 2490),  
                              '22': (5565, 1465), '23': (5690, 1465), '24': (5825, 1465), '25': (5950, 1465), '26': (6090, 1465),
                              '27': (5565, 1655), '28': (5690, 1655), '29': (5825, 1655), '30': (5950, 1655), '31': (6090, 1655),
                              '32': (5565, 1830), '33': (5690, 1830), '34': (5825, 1830), '35': (5950, 1830), '36': (6090, 1830), 
                              }

sort_slots = {'37': (6350, 2020), '38': (6485, 2020),
                           '39': (6350, 2140), '40': (6485, 2140),
                           '41': (6350, 2275), '42': (6485, 2275),
                           '43': (6350, 2415), '44': (6485, 2415),
                           '45': (6350, 2530), '46': (6485, 2530),
                          }

put_away_2f_3f_slots = {'47': (6535, 1910), '48': (6665, 1910), '49': (6770, 1910), '50': (6890, 1910),
                                '51': (6665, 2020), '52': (6890, 2020),
                                '53': (6665, 2140), '54': (6770, 2140), '55': (6890, 2140),
                                '56': (6665, 2255), '57': (6770, 2255), '58': (6890, 2255),
                                '59': (6665, 2430), '60': (6770, 2430), '61': (6890, 2430),
                                '62': (6665, 2550), '63': (6770, 2550), '64': (6890, 2550),
                               }

put_away_4f_5f_slots = {'65': (6390, 1410), '66': (6515, 1410), '67': (6640, 1410), '68': (6760, 1410), '69': (6900, 1410),
                                '70': (6390, 1525), '71': (6515, 1525), '72': (6640, 1525), '73': (6760, 1525), '74': (6900, 1525),
                                '75': (6390, 1640), '76': (6515, 1640), '77': (6640, 1640), '78': (6760, 1640), '79': (6900, 1640),
                               }


def slots_with_enum(slots, enum):
    return {int(k): ((x,y),enum) for k, (x,y) in slots.items()}

ptokai_box_info = {
    **slots_with_enum(inspect_slots,Slot.INSPECT), 
    **slots_with_enum(sort_slots,Slot.SORT),
    **slots_with_enum(put_away_2f_3f_slots,Slot.PUT_AWAY_2F_3F),
    **slots_with_enum(put_away_4f_5f_slots,Slot.PUT_AWAY_4F_5F)
}

print(
    ptokai_box_info[1]
)
