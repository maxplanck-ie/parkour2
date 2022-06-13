import json

from rest_framework.response import Response
from rest_framework.decorators import action


class MultiEditMixin:
    """
    Provides the `edit()` action, which updates multiple objects.
    """

    @action(methods=['post'], detail=False)
    def edit(self, request):
        """ Update multiple objects. """

        if request.is_ajax():
            post_data = request.data.get('data', [])
        else:
            post_data = json.loads(request.data.get('data', '[]'))

        if not post_data:
            return Response({
                'success': False,
                'message': 'Invalid payload.',
            }, 400)

        ids = []
        for obj in post_data:
            try:
                ids.append(int(obj['pk']))
            except (KeyError, ValueError):
                continue

        objects = self._get_model().objects.filter(pk__in=ids)
        serializer = self.get_serializer(
            data=post_data, instance=objects, many=True)

        if serializer.is_valid():
            serializer.save()
            return Response({'success': True})
        else:
            # Try to update valid lanes
            valid_data = [item[1] for item in zip(serializer.errors, post_data)
                          if not item[0]]

            if any(valid_data):
                self._update_valid(valid_data)
                return Response({
                    'success': True,
                    'message': 'Some records cannot be updated.',
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid payload.',
                }, 400)

    def _update_valid(self, data):
        """ Update valid objects. """
        ids = [x['pk'] for x in data]
        objects = self._get_model().objects.filter(pk__in=ids)
        serializer = self.get_serializer(
            data=data, instance=objects, many=True)
        serializer.is_valid()
        serializer.save()

    def _get_model(self):
        return self.get_serializer().Meta.model


class LibrarySampleMultiEditMixin(object):
    """
    Provides the `edit()` action, which updates multiple objects and deals with
    both Library and Sample instances.
    """

    @action(methods=['post'], detail=False)
    def edit(self, request):
        """ Update multiple libraries or samples. """
        if request.is_ajax():
            post_data = request.data.get('data', [])
        else:
            post_data = json.loads(request.data.get('data', '[]'))

        if not post_data:
            return Response({
                'success': False,
                'message': 'Invalid payload.',
            }, 400)

        library_ids, sample_ids, library_post_data, sample_post_data = \
            self._separate_data(post_data)

        libraries_ok, libraries_no_invalid = self._update_objects(
            self.library_model, self.library_serializer,
            library_ids, library_post_data,
        )

        samples_ok, samples_no_invalid = self._update_objects(
            self.sample_model, self.sample_serializer,
            sample_ids, sample_post_data
        )

        result = [libraries_ok, libraries_no_invalid,
                  samples_ok, samples_no_invalid]
        result = [x for x in result if x is not None]

        if result.count(True) == len(result):
            return Response({'success': True})
        elif result.count(False) == len(result):
            return Response({
                'success': False,
                'message': 'Invalid payload.',
            }, 400)
        else:
            return Response({
                'success': True,
                'message': 'Some records cannot be updated.',
            })

    def _separate_data(self, data):
        """
        Separate library and sample data, ignoring objects without
        either 'id' or 'record_type' or non-integer id.
        """
        library_ids = []
        sample_ids = []
        library_data = []
        sample_data = []

        for obj in data:
            try:
                if obj['record_type'] == 'Library':
                    library_ids.append(int(obj['pk']))
                    library_data.append(obj)
                elif obj['record_type'] == 'Sample':
                    sample_ids.append(int(obj['pk']))
                    sample_data.append(obj)
            except (KeyError, ValueError):
                continue

        return library_ids, sample_ids, library_data, sample_data

    def _update_objects(self, model_class, serializer_class, ids, data):
        """
        Update multiple objects with a given model class and a
        serializer class.
        """
        objects_ok = True
        no_invalid = True

        # objects = model_class.objects.filter(pk__in=ids, status=1)  # Inc. L.
        objects = model_class.objects.filter(pk__in=ids)

        if not objects:
            return None, None

        serializer = serializer_class(data=data, instance=objects, many=True)

        if serializer.is_valid():
            serializer.save()
        else:
            # Try to update valid objects
            valid_data = [item[1] for item in zip(serializer.errors, data)
                          if not item[0]]

            if any(valid_data):
                new_ids = [x['pk'] for x in valid_data]
                self._update_valid(
                    model_class, serializer_class, new_ids, valid_data)
            else:
                objects_ok = False
            no_invalid = False

        return objects_ok, no_invalid

    def _update_valid(self, model_class, serializer_class, ids, valid_data):
        """ Update valid objects. """
        objects = model_class.objects.filter(pk__in=ids)
        serializer = serializer_class(
            data=valid_data, instance=objects, many=True)
        serializer.is_valid()
        serializer.save()
