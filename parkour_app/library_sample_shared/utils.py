from .models import IndexType


def get_indices_ids(obj):
    """ Get Index I7/I5 ids for a given library/sample. """

    try:
        index_type = IndexType.objects.get(pk=obj.index_type.pk)
        index_i7 = index_type.indices_i7.get(index=obj.index_i7)
        index_i7_id = index_i7.index_id
    except Exception:
        index_i7_id = ''

    try:
        index_type = IndexType.objects.get(pk=obj.index_type.pk)
        index_i5 = index_type.indices_i5.get(index=obj.index_i5)
        index_i5_id = index_i5.index_id
    except Exception:
        index_i5_id = ''

    return index_i7_id, index_i5_id


def move_other_to_end(data):
    """ Move 'Other' option to the end of the list. """
    result = []
    result.extend(data)

    other = [x for x in result if x['name'] == 'Other']
    if other:
        index = result.index(other[0])
        result.append(result.pop(index))

    return result
