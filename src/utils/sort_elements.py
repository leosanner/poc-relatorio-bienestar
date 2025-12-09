def sort_by_d(content_obj):

    if not isinstance(content_obj, list):
        raise TypeError("A função deve receber uma lista.")

    if len(content_obj) <= 1:
        return content_obj

    if isinstance(content_obj[0], dict):
        return sorted(content_obj, key=lambda x: x["D"], reverse=False)

    if isinstance(content_obj[0], list):
        return sorted(content_obj, key=lambda x: x[-1], reverse=False)


def remove_duplicates(content_obj):
    if not isinstance(content_obj, list):
        raise TypeError("A função deve receber uma lista.")

    if len(content_obj) <= 1:
        return content_obj

    unique_names = []
    unique_results = []

    if isinstance(content_obj[0], dict):
        for d in content_obj:
            if d.get("nome"):
                name = d.get("nome").lower()

                if name not in unique_names:
                    unique_names.append(name)
                    unique_results.append(d)

        return unique_results

    if isinstance(content_obj[0], list):
        for d in content_obj:
            if isinstance(d[0], str):
                name = d[0].lower()

                if name not in unique_names:
                    unique_names.append(name)
                    unique_results.append(d)

        return unique_results
