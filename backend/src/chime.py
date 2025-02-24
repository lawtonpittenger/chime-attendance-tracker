
import asyncio
import scribe
from playwright.async_api import TimeoutError
from datetime import datetime

async def meeting(page):
    print("Getting meeting link.")
    await page.goto(f"https://app.chime.aws/meetings/{scribe.meeting_id}")

    print("Entering name.")
    try:
        name_text_element = await page.wait_for_selector('#name')
    except TimeoutError:
        print("Your scribe was unable to join the meeting.")
        return
    else:
        await name_text_element.type(scribe.scribe_identity)
        await name_text_element.press('Tab')
        await page.keyboard.press('Enter')

    print("Clicking mute button.")
    mute_checkbox_element = await page.wait_for_selector('text="Join muted"')
    await mute_checkbox_element.click()

    print("Clicking join button.")
    join_button_element = await page.wait_for_selector(
        'button[data-testid="button"][aria-label="Join"]'
    )
    await join_button_element.click()

    print("Waiting for meeting access.")
    try:
        await page.wait_for_selector(
            'button[data-testid="button"][aria-label^="Open chat panel"]',
            timeout=scribe.waiting_timeout
        )
    except TimeoutError:
        print("Your scribe was not admitted into the meeting.")
        return

    print("Opening attendees panel.")
    attendees_panel_element = await page.wait_for_selector(
        'button[data-testid="button"][aria-label^="Open attendees panel"]'
    )
    await attendees_panel_element.click()

    async def attendee_change(number: int):
        if number <= 1:
            print("Your scribe got lonely and left.")
            await page.goto("about:blank")

    await page.expose_function("attendeeChange", attendee_change)

    print("Listening for attendee changes.")
    await page.evaluate('''
        const targetNode = document.querySelector('button[data-testid="collapse-container"][aria-label^="Present"]')
        const config = { characterData: true, subtree: true }

        const callback = (mutationList, observer) => {
            attendeeChange(parseInt(mutationList[mutationList.length - 1].target.textContent))
        }

        const observer = new MutationObserver(callback)
        observer.observe(targetNode, config)
    ''')

    await page.expose_function("speakerChange", scribe.speaker_change)

    print("Listening for speaker changes.")
    await page.evaluate('''
        const targetNode = document.querySelector('.activeSpeakerCell ._3yg3rB2Xb_sfSzRXkm8QT-')
        const config = { characterData: true, subtree: true }

        const callback = (mutationList, observer) => {
            for (const mutation of mutationList) {
                const new_speaker = mutation.target.textContent
                if (new_speaker != "No one") speakerChange(new_speaker)
            }
        }

        const observer = new MutationObserver(callback)
        observer.observe(targetNode, config)

        const initial_speaker = targetNode.textContent
        if (initial_speaker != "No one") speakerChange(initial_speaker)
    ''')

    print("Waiting for meeting end.")
    try:
        await page.wait_for_selector('button[id="endMeeting"]', state="detached", timeout=scribe.meeting_timeout)
        print("Meeting ended.")
    except TimeoutError:
        print("Meeting timed out.")
