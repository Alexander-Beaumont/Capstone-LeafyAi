import { test} from 'vitest'
import { render} from 'vitest-browser-react';
import { expect } from 'vitest';
import Navbar from '../components/Navbar';
import { MemoryRouter } from 'react-router';

//Note this is just example test cases 

test('adds 1 + 2 to equal 3', () => {
  expect(1 + 2).toBe(3)
})

test("renders navbar", async () => {
    const screen = await render(
        <MemoryRouter>
            <Navbar/>
        </MemoryRouter>
    );

    await expect.element(
        screen.getByText("Sign Up")
    ).toBeVisible();
});