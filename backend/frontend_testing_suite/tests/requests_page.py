import csv
import os
from datetime import datetime

import pytest
import utilities
from playwright.sync_api import Page, expect

CSV_DATA = os.path.dirname(os.path.realpath(__file__)) + "/../data/"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    my_screen_size = {
        "width": 2560,
        "height": 1440,
    }
    return {
        **browser_context_args,
        "viewport": my_screen_size,
        "device_scale_factor": 2,
    }


def test_requests_page(page: Page):
    utilities.pretest_login(page)

    addRequestButton = page.locator("a.pl-add-request-button")
    descriptionTextarea = page.locator("div.pl-description>div>div>div>textarea")
    addBatchButton = page.locator("a.pl-batch-add-button")
    libraryCardButton = page.locator("a.pl-library-card-button")
    sampleCardButton = page.locator("a.pl-sample-card-button")
    createEmptyRowButton = page.locator("a.pl-create-empty-records-button")
    nameInput = page.locator("input[name='name']")
    nucleicAcidInput = page.locator("input[name='nucleic_acid_type']")
    libraryProtocolInput = page.locator("input[name='library_protocol']")
    libraryTypeInput = page.locator("input[name='library_type']")
    concentrationInput = page.locator("input[name='concentration']")
    meanFragmentSizeInput = page.locator("input[name='mean_fragment_size']")
    indexTypeInput = page.locator("input[name='index_type']")
    indexReadsInput = page.locator("input[name='index_reads']")
    indexi7Input = page.locator("input[name='index_i7']")
    indexi5Input = page.locator("input[name='index_i5']")
    rnaQualityInput = page.locator("input[name='rna_quality']")
    readLengthInput = page.locator("input[name='read_length']")
    sequencingDepthInput = page.locator("input[name='sequencing_depth']")
    organismInput = page.locator("input[name='organism']")
    commentsInput = page.locator("input[name='comments']")
    updateButton = page.locator("a.x-row-editor-update-button")
    addSaveRequestButton = page.get_by_text("Save").nth(1)
    saveAddedRequestbutton = page.get_by_text("Save").nth(0)
    addSuccessNotification = page.get_by_text("The request has been auto-saved.")
    finalSuccessNotification = page.get_by_text("Changes have been saved successfully.")

    addRequestButton.click()
    expect(page.get_by_text("New Request")).to_be_visible()
    descriptionTextarea.fill("This is libraries' description text.")
    addBatchButton.click()
    expect(page.get_by_text("Add Libraries/Samples")).to_be_visible()
    libraryCardButton.click()
    expect(page.get_by_text("Add Libraries")).to_be_visible()
    with open(
        CSV_DATA + "library_request.csv",
        newline="",
        encoding="utf-8",
    ) as library_csv_file:
        spamreader = csv.reader(library_csv_file, delimiter=",", quotechar='"')
        for index, row in enumerate(spamreader):
            if index > 0:
                createEmptyRowButton.click()
                editRow = page.locator(
                    "div.x-grid-cell-inner-row-numberer"
                ).get_by_text(str(index))
                editRow.click()
                nameInput.fill(row[0])
                libraryProtocolInput.fill(row[1])
                page.keyboard.press("Enter")
                libraryTypeInput.fill(row[2])
                concentrationInput.fill(row[3])
                meanFragmentSizeInput.fill(row[4])
                indexTypeInput.fill(row[5])
                page.keyboard.press("Enter")
                indexReadsInput.fill(row[6])
                page.keyboard.press("Enter")
                indexi7Input.fill(row[7])
                indexi5Input.fill(row[8])
                readLengthInput.fill(row[9])
                sequencingDepthInput.fill(row[10])
                organismInput.fill(row[11])
                commentsInput.fill(row[12])
                updateButton.click()
    addSaveRequestButton.click()
    # expect(page.get_by_text("New Request")).to_be_visible()
    saveAddedRequestbutton.click()
    expect(addSuccessNotification).to_be_visible()
    expect(finalSuccessNotification).to_be_visible()
    addRequestButton.click()
    # expect(page.get_by_text("New Request")).to_be_visible()
    descriptionTextarea.fill("This is samples' description.")
    addBatchButton.click()
    expect(page.get_by_text("Add Libraries/Samples")).to_be_visible()
    sampleCardButton.click()
    expect(page.get_by_text("Add Samples")).to_be_visible()
    with open(
        CSV_DATA + "sample_request.csv",
        newline="",
        encoding="utf-8",
    ) as sample_csv_file:
        spamreader = csv.reader(sample_csv_file, delimiter=",", quotechar='"')
        for index, row in enumerate(spamreader):
            if index > 0:
                createEmptyRowButton.click()
                editRow = page.locator(
                    "div.x-grid-cell-inner-row-numberer"
                ).get_by_text(str(index))
                editRow.click()
                nameInput.fill(row[0])
                nucleicAcidInput.fill(row[1])
                page.keyboard.press("Enter")
                libraryProtocolInput.fill(row[2])
                page.keyboard.press("Enter")
                libraryTypeInput.fill(row[3])
                concentrationInput.fill(row[4])
                rnaQualityInput.fill(row[5])
                readLengthInput.fill(row[6])
                sequencingDepthInput.fill(row[7])
                organismInput.fill(row[8])
                commentsInput.fill(row[9])
                updateButton.click()
    addSaveRequestButton.click()
    # expect(page.get_by_text("New Request")).to_be_visible()
    saveAddedRequestbutton.click()
    expect(addSuccessNotification).to_be_visible()
    expect(finalSuccessNotification).to_be_visible()

    page.get_by_text("Libraries & Samples").click()
    page.locator(
        "#librariesTable-body>div>div>table>tbody>tr>td>.x-grid-cell-inner-treecolumn>.x-tree-expander"
    ).nth(0).click()
    with open(
        CSV_DATA + "sample_request.csv",
        newline="",
        encoding="utf-8",
    ) as sample_csv_file:
        spamreader = csv.reader(sample_csv_file, delimiter=",", quotechar='"')
        for index, row in enumerate(spamreader):
            if index > 0:
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(1)>div>span"
                    ).nth(index)
                ).to_contain_text(str(row[0]))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(6)>div"
                    ).nth(index)
                ).to_contain_text(datetime.today().strftime("%d.%m.%Y"))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(7)>div"
                    ).nth(index)
                ).to_contain_text(str(row[1]))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(8)>div"
                    ).nth(index)
                ).to_contain_text(str(row[2]))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(9)>div"
                    ).nth(index)
                ).to_contain_text(str(row[3]))
                assert page.locator(
                    "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(10)>div"
                ).nth(index).inner_text() in str(row[4]), f"Values are not matching."
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(11)>div"
                    ).nth(index)
                ).to_contain_text(str(row[5]))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(17)>div"
                    ).nth(index)
                ).to_contain_text(str(row[6]))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(18)>div"
                    ).nth(index)
                ).to_contain_text(str(row[7]))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(19)>div"
                    ).nth(index)
                ).to_contain_text(str(row[8]))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(20)>div"
                    ).nth(index)
                ).to_contain_text(str(row[9]))

    page.locator(
        "#librariesTable-body>div>div>table>tbody>tr>td>.x-grid-cell-inner-treecolumn>.x-tree-expander"
    ).nth(0).click()
    page.locator(
        "#librariesTable-body>div>div>table>tbody>tr>td>.x-grid-cell-inner-treecolumn>.x-tree-expander"
    ).nth(1).click()
    with open(
        CSV_DATA + "library_request.csv",
        newline="",
        encoding="utf-8",
    ) as library_csv_file:
        spamreader = csv.reader(library_csv_file, delimiter=",", quotechar='"')
        for index, row in enumerate(spamreader):
            if index > 0:
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(1)>div>span"
                    ).nth(index + 1)
                ).to_contain_text(str(row[0]))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(6)>div"
                    ).nth(index + 1)
                ).to_contain_text(datetime.today().strftime("%d.%m.%Y"))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(8)>div"
                    ).nth(index + 1)
                ).to_contain_text(str(row[1]))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(9)>div"
                    ).nth(index + 1)
                ).to_contain_text(str(row[2]))
                assert page.locator(
                    "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(10)>div"
                ).nth(index + 1).inner_text() in str(
                    row[3]
                ), f"Values are not matching."
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(12)>div"
                    ).nth(index + 1)
                ).to_contain_text(str(row[4]))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(13)>div"
                    ).nth(index + 1)
                ).to_contain_text(str(row[5]))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(14)>div"
                    ).nth(index + 1)
                ).to_contain_text(str(row[6]))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(15)>div"
                    ).nth(index + 1)
                ).to_contain_text(str(row[7]))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(16)>div"
                    ).nth(index + 1)
                ).to_contain_text(str(row[8]))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(17)>div"
                    ).nth(index + 1)
                ).to_contain_text(str(row[9]))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(18)>div"
                    ).nth(index + 1)
                ).to_contain_text(str(row[10]))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(19)>div"
                    ).nth(index + 1)
                ).to_contain_text(str(row[11]))
                expect(
                    page.locator(
                        "#librariesTable-body>div>div>table>tbody>tr>td:nth-child(20)>div"
                    ).nth(index + 1)
                ).to_contain_text(str(row[12]))
