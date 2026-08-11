def insertion_sort_by_field(students: list[dict], field: str) -> None:
    """Sorts `students` in place, ascending, by `field` (e.g. "age" or "name").

    Hand-written Insertion Sort: no sorted()/.sort()/any built-in sorting
    utility is used anywhere in this function.

    Best case O(n): the list is already sorted, so the inner while loop
    never shifts anything -- each outer-loop pass does one comparison and
    stops. Worst case O(n^2): the list is in reverse order, so for each
    element the inner while loop has to shift every previously-placed
    element one position to the right before inserting the key, giving
    roughly n*(n-1)/2 shifts total.
    """
    for i in range(1, len(students)):
        key = students[i]
        j = i - 1
        while j >= 0 and students[j][field] > key[field]:
            students[j + 1] = students[j]
            j -= 1
        students[j + 1] = key


def binary_search_by_name(sorted_by_name_list: list[dict], name: str):
    """Hand-written iterative Binary Search over a list already sorted
    alphabetically by "name". Returns the matching student dict, or -1
    if not found.

    Binary Search only works because each comparison decides which half
    of the list to discard -- that's only valid if the list is already
    ordered on the field being searched. On an unsorted list, "greater"
    or "smaller" than the midpoint tells you nothing about which half the
    target is in.
    """
    low = 0
    high = len(sorted_by_name_list) - 1

    while low <= high:
        mid = low + (high - low) // 2
        mid_name = sorted_by_name_list[mid]["name"]

        if mid_name == name:
            return sorted_by_name_list[mid]
        elif mid_name < name:
            low = mid + 1
        else:
            high = mid - 1

    return -1


def format_roster_report(students: list[dict]) -> str:
    """Builds a multi-line string, one line per student, in the form:
    "[Age {age}] {name} <{email}>"
    """
    lines = []
    for student in students:
        line = f"[Age {student['age']}] {student['name']} <{student['email']}>"
        lines.append(line)
    return "\n".join(lines)


def count_students_meeting_min_age(students: list[dict], min_age: int) -> int:
    """Returns how many students have age >= min_age."""
    count = 0
    for student in students:
        if student["age"] >= min_age:
            count += 1
    return count